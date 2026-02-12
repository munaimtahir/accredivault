from datetime import timedelta
from typing import Any

from django.db.models import Max, Q, QuerySet
from django.utils import timezone

from apps.compliance.models import ControlStatusCache, ControlVerification, EvidenceRule
from apps.evidence.models import ControlEvidenceLink, EvidenceItem
from apps.standards.models import Control


def get_section_code_from_control(control_code: str) -> str:
    parts = (control_code or '').split('-')
    if len(parts) == 3 and parts[0] and parts[1] and parts[2]:
        return parts[1]
    return 'UNK'


def fetch_applicable_rules(control: Control) -> QuerySet[EvidenceRule]:
    section_code = get_section_code_from_control(control.control_code)
    return EvidenceRule.objects.filter(
        standard_pack=control.standard_pack,
        enabled=True,
    ).filter(
        Q(scope_type=EvidenceRule.SCOPE_CONTROL, control=control)
        | Q(scope_type=EvidenceRule.SCOPE_SECTION, section_code=section_code)
    )


def fetch_linked_evidence(control: Control) -> QuerySet[EvidenceItem]:
    return (
        EvidenceItem.objects
        .filter(control_links__control=control)
        .prefetch_related('files')
        .order_by('-event_date', '-created_at')
        .distinct()
    )


def evaluate_rule(rule: EvidenceRule, evidence_items, today) -> dict[str, Any]:
    matched = list(evidence_items)

    if rule.acceptable_categories:
        matched = [ev for ev in matched if ev.category in rule.acceptable_categories]
    if rule.acceptable_subtypes:
        matched = [ev for ev in matched if ev.subtype in rule.acceptable_subtypes]

    matched_count = len(matched)
    last_match_date = max((ev.event_date for ev in matched), default=None)

    result = {
        'rule_id': str(rule.id),
        'satisfied': False,
        'status_hint': 'MISSING',
        'due_date': None,
        'matched_count': matched_count,
        'last_match_date': last_match_date,
    }

    if rule.rule_type == EvidenceRule.RULE_ONE_TIME:
        result['satisfied'] = matched_count >= rule.min_items
        result['status_hint'] = 'OK' if result['satisfied'] else 'MISSING'
        return result

    if rule.rule_type == EvidenceRule.RULE_FREQUENCY:
        if not last_match_date:
            result['status_hint'] = 'OVERDUE'
            return result
        due_date = last_match_date + timedelta(days=rule.frequency_days)
        result['due_date'] = due_date
        result['satisfied'] = due_date >= today
        result['status_hint'] = 'OK' if result['satisfied'] else 'OVERDUE'
        return result

    if rule.rule_type in (EvidenceRule.RULE_ROLLING_WINDOW, EvidenceRule.RULE_COUNT_IN_WINDOW):
        window_start = today - timedelta(days=rule.window_days)
        count_in_window = sum(1 for ev in matched if ev.event_date >= window_start)
        due_date = (last_match_date + timedelta(days=rule.window_days)) if last_match_date else None
        required_count = max(1, rule.min_items)

        result['matched_count'] = count_in_window
        result['due_date'] = due_date
        result['satisfied'] = count_in_window >= required_count
        result['status_hint'] = 'OK' if result['satisfied'] else 'OVERDUE'
        return result

    if rule.rule_type == EvidenceRule.RULE_EXPIRY:
        valid = [ev for ev in matched if ev.valid_until and ev.valid_until >= today]
        valid_until_dates = sorted(ev.valid_until for ev in valid)
        result['matched_count'] = len(valid)
        result['satisfied'] = len(valid) >= 1
        result['due_date'] = valid_until_dates[0] if valid_until_dates else None
        result['status_hint'] = 'OK' if result['satisfied'] else 'OVERDUE'
        result['last_match_date'] = max((ev.event_date for ev in valid), default=None)
        return result

    return result


def compute_control_status(control: Control) -> dict[str, Any]:
    today = timezone.localdate()
    rules = list(fetch_applicable_rules(control))
    evidence_items = list(fetch_linked_evidence(control))

    last_evidence_date = max((ev.event_date for ev in evidence_items), default=None)
    latest_linked_at = (
        ControlEvidenceLink.objects
        .filter(control=control)
        .aggregate(max_linked_at=Max('linked_at'))
        .get('max_linked_at')
    )

    rule_results = [evaluate_rule(rule, evidence_items, today) for rule in rules]

    if not evidence_items:
        computed_status = 'NOT_STARTED'
    else:
        any_overdue = any(
            rr['status_hint'] == 'OVERDUE' or (rr['satisfied'] is False and rr['due_date'] is not None and rr['due_date'] < today)
            for rr in rule_results
        )
        all_satisfied = bool(rule_results) and all(rr['satisfied'] for rr in rule_results)

        if any_overdue:
            computed_status = 'OVERDUE'
        elif all_satisfied:
            if any(rule.requires_verification for rule in rules):
                latest_verified = (
                    ControlVerification.objects
                    .filter(control=control, status=ControlVerification.STATUS_VERIFIED)
                    .order_by('-verified_at')
                    .first()
                )
                verification_fresh = bool(
                    latest_verified
                    and (
                        latest_linked_at is None
                        or (
                            latest_verified.evidence_snapshot_at is not None
                            and latest_verified.evidence_snapshot_at >= latest_linked_at
                        )
                    )
                )
                computed_status = 'VERIFIED' if verification_fresh else 'READY'
            else:
                computed_status = 'READY'
        else:
            computed_status = 'IN_PROGRESS'

    due_dates = [rr['due_date'] for rr in rule_results if rr.get('due_date') is not None]
    next_due_date = min(due_dates) if due_dates else None

    latest_verified = (
        ControlVerification.objects
        .filter(control=control, status=ControlVerification.STATUS_VERIFIED)
        .order_by('-verified_at')
        .first()
    )
    verification_fresh = bool(
        latest_verified
        and (
            latest_linked_at is None
            or (
                latest_verified.evidence_snapshot_at is not None
                and latest_verified.evidence_snapshot_at >= latest_linked_at
            )
        )
    )

    details_json = {
        'section_code': get_section_code_from_control(control.control_code),
        'last_evidence_date': last_evidence_date.isoformat() if last_evidence_date else None,
        'next_due_date': next_due_date.isoformat() if next_due_date else None,
        'rule_results': [
            {
                **rr,
                'due_date': rr['due_date'].isoformat() if rr['due_date'] else None,
                'last_match_date': rr['last_match_date'].isoformat() if rr['last_match_date'] else None,
            }
            for rr in rule_results
        ],
        'latest_verified_at': latest_verified.verified_at.isoformat() if latest_verified else None,
        'verification_fresh': verification_fresh,
    }

    return {
        'control_id': control.id,
        'computed_status': computed_status,
        'last_evidence_date': last_evidence_date,
        'next_due_date': next_due_date,
        'details_json': details_json,
    }


def recompute_and_persist(control: Control) -> ControlStatusCache:
    computed = compute_control_status(control)
    cache, _created = ControlStatusCache.objects.update_or_create(
        control=control,
        defaults={
            'computed_status': computed['computed_status'],
            'last_evidence_date': computed['last_evidence_date'],
            'next_due_date': computed['next_due_date'],
            'details_json': computed['details_json'],
        },
    )
    return cache
