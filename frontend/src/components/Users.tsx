import React, { useEffect, useState } from 'react';
import { api, type UserList } from '../api';
import './Users.css';

const CANONICAL_ROLES = ['ADMIN', 'MANAGER', 'AUDITOR', 'DATA_ENTRY', 'VIEWER'];

const Users: React.FC = () => {
  const [users, setUsers] = useState<UserList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [editUser, setEditUser] = useState<UserList | null>(null);
  const [resetUserId, setResetUserId] = useState<number | null>(null);

  const [createUsername, setCreateUsername] = useState('');
  const [createPassword, setCreatePassword] = useState('');
  const [createFirstName, setCreateFirstName] = useState('');
  const [createLastName, setCreateLastName] = useState('');
  const [createRoles, setCreateRoles] = useState<string[]>([]);
  const [createError, setCreateError] = useState<string | null>(null);
  const [createBusy, setCreateBusy] = useState(false);

  const [editFirstName, setEditFirstName] = useState('');
  const [editLastName, setEditLastName] = useState('');
  const [editActive, setEditActive] = useState(true);
  const [editRoles, setEditRoles] = useState<string[]>([]);
  const [editError, setEditError] = useState<string | null>(null);
  const [editBusy, setEditBusy] = useState(false);

  const [resetPassword, setResetPassword] = useState('');
  const [resetError, setResetError] = useState<string | null>(null);
  const [resetBusy, setResetBusy] = useState(false);

  const loadUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getUsers();
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const toggleCreateRole = (role: string) => {
    setCreateRoles((prev) =>
      prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]
    );
  };

  const toggleEditRole = (role: string) => {
    setEditRoles((prev) =>
      prev.includes(role) ? prev.filter((r) => r !== role) : [...prev, role]
    );
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createUsername || !createPassword) {
      setCreateError('Username and password are required.');
      return;
    }
    if (createPassword.length < 8) {
      setCreateError('Password must be at least 8 characters.');
      return;
    }
    try {
      setCreateBusy(true);
      setCreateError(null);
      await api.createUser({
        username: createUsername,
        password: createPassword,
        first_name: createFirstName || undefined,
        last_name: createLastName || undefined,
        roles: createRoles,
      });
      setCreateOpen(false);
      setCreateUsername('');
      setCreatePassword('');
      setCreateFirstName('');
      setCreateLastName('');
      setCreateRoles([]);
      await loadUsers();
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create user');
    } finally {
      setCreateBusy(false);
    }
  };

  const openEdit = (u: UserList) => {
    setEditUser(u);
    setEditFirstName(u.first_name);
    setEditLastName(u.last_name);
    setEditActive(u.is_active);
    setEditRoles(u.roles || []);
    setEditError(null);
  };

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editUser) return;
    try {
      setEditBusy(true);
      setEditError(null);
      await api.updateUser(editUser.id, {
        first_name: editFirstName,
        last_name: editLastName,
        is_active: editActive,
        roles: editRoles,
      });
      setEditUser(null);
      await loadUsers();
    } catch (err) {
      setEditError(err instanceof Error ? err.message : 'Failed to update user');
    } finally {
      setEditBusy(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resetUserId || !resetPassword) return;
    if (resetPassword.length < 8) {
      setResetError('Password must be at least 8 characters.');
      return;
    }
    try {
      setResetBusy(true);
      setResetError(null);
      await api.resetUserPassword(resetUserId, resetPassword);
      setResetUserId(null);
      setResetPassword('');
    } catch (err) {
      setResetError(err instanceof Error ? err.message : 'Failed to reset password');
    } finally {
      setResetBusy(false);
    }
  };

  return (
    <div className="users-container">
      <header className="users-header">
        <h1>User Management</h1>
        <button className="btn-primary" onClick={() => setCreateOpen(true)}>
          Create User
        </button>
      </header>

      {loading && <div className="loading">Loading users...</div>}
      {error && <div className="error">Error: {error}</div>}

      {!loading && !error && (
        <div className="users-table-wrapper">
          <table className="users-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Name</th>
                <th>Roles</th>
                <th>Active</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.username}</td>
                  <td>
                    {u.first_name} {u.last_name}
                  </td>
                  <td>{u.roles?.join(', ') || '-'}</td>
                  <td>{u.is_active ? 'Yes' : 'No'}</td>
                  <td>
                    <button className="btn-secondary btn-small" onClick={() => openEdit(u)}>
                      Edit
                    </button>
                    <button
                      className="btn-secondary btn-small"
                      onClick={() => setResetUserId(u.id)}
                      style={{ marginLeft: '0.35rem' }}
                    >
                      Reset Password
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {createOpen && (
        <div className="modal-overlay" onClick={() => setCreateOpen(false)}>
          <div className="modal-card users-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Create User</h3>
            <form onSubmit={handleCreate}>
              <div className="form-group">
                <label>Username *</label>
                <input
                  value={createUsername}
                  onChange={(e) => setCreateUsername(e.target.value)}
                  placeholder="username"
                />
              </div>
              <div className="form-group">
                <label>Password * (min 8 chars)</label>
                <input
                  type="password"
                  value={createPassword}
                  onChange={(e) => setCreatePassword(e.target.value)}
                  placeholder="password"
                />
              </div>
              <div className="form-group">
                <label>First Name</label>
                <input value={createFirstName} onChange={(e) => setCreateFirstName(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Last Name</label>
                <input value={createLastName} onChange={(e) => setCreateLastName(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Roles</label>
                <div className="roles-checkboxes">
                  {CANONICAL_ROLES.map((r) => (
                    <label key={r}>
                      <input
                        type="checkbox"
                        checked={createRoles.includes(r)}
                        onChange={() => toggleCreateRole(r)}
                      />{' '}
                      {r}
                    </label>
                  ))}
                </div>
              </div>
              {createError && <div className="error-banner">{createError}</div>}
              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={createBusy}>
                  Create
                </button>
                <button type="button" className="btn-secondary" onClick={() => setCreateOpen(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {editUser && (
        <div className="modal-overlay" onClick={() => setEditUser(null)}>
          <div className="modal-card users-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Edit User: {editUser.username}</h3>
            <form onSubmit={handleEdit}>
              <div className="form-group">
                <label>First Name</label>
                <input value={editFirstName} onChange={(e) => setEditFirstName(e.target.value)} />
              </div>
              <div className="form-group">
                <label>Last Name</label>
                <input value={editLastName} onChange={(e) => setEditLastName(e.target.value)} />
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={editActive}
                    onChange={(e) => setEditActive(e.target.checked)}
                  />{' '}
                  Active
                </label>
              </div>
              <div className="form-group">
                <label>Roles</label>
                <div className="roles-checkboxes">
                  {CANONICAL_ROLES.map((r) => (
                    <label key={r}>
                      <input
                        type="checkbox"
                        checked={editRoles.includes(r)}
                        onChange={() => toggleEditRole(r)}
                      />{' '}
                      {r}
                    </label>
                  ))}
                </div>
              </div>
              {editError && <div className="error-banner">{editError}</div>}
              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={editBusy}>
                  Save
                </button>
                <button type="button" className="btn-secondary" onClick={() => setEditUser(null)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {resetUserId && (
        <div className="modal-overlay" onClick={() => setResetUserId(null)}>
          <div className="modal-card users-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Reset Password</h3>
            <form onSubmit={handleResetPassword}>
              <div className="form-group">
                <label>New Password * (min 8 chars)</label>
                <input
                  type="password"
                  value={resetPassword}
                  onChange={(e) => setResetPassword(e.target.value)}
                  placeholder="new password"
                />
              </div>
              {resetError && <div className="error-banner">{resetError}</div>}
              <div className="form-actions">
                <button type="submit" className="btn-primary" disabled={resetBusy}>
                  Reset
                </button>
                <button type="button" className="btn-secondary" onClick={() => setResetUserId(null)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;
