import React, { useState, useEffect } from 'react';

const DEPARTMENTS = [
  'Computer Science',
  'Information Technology',
  'Electronics & Communication',
  'Mechanical Engineering',
  'Civil Engineering',
  'Electrical Engineering',
  'Data Science',
  'Artificial Intelligence',
  'Business Administration',
];

export default function StudentForm({ student, isOpen, onClose, onSubmit, isSubmitting }) {
  const isEdit = !!student;

  const [formData, setFormData] = useState({
    student_id: '',
    full_name: '',
    department: DEPARTMENTS[0],
    year_of_study: 1,
    email: '',
    status: 'active',
  });

  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (student) {
      setFormData({
        student_id: student.student_id || '',
        full_name: student.full_name || '',
        department: student.department || DEPARTMENTS[0],
        year_of_study: student.year_of_study || 1,
        email: student.email || '',
        status: student.status || 'active',
      });
    } else {
      setFormData({
        student_id: '',
        full_name: '',
        department: DEPARTMENTS[0],
        year_of_study: 1,
        email: '',
        status: 'active',
      });
    }
    setErrors({});
  }, [student, isOpen]);

  if (!isOpen) return null;

  const validate = () => {
    const errs = {};
    if (!isEdit) {
      if (!formData.student_id.trim()) {
        errs.student_id = 'Student ID is required.';
      } else if (!/^[A-Za-z0-9_-]{2,30}$/.test(formData.student_id.trim())) {
        errs.student_id = 'Must be 2-30 alphanumeric characters or hyphens.';
      }
    }

    if (!formData.full_name.trim()) {
      errs.full_name = 'Full name is required.';
    } else if (formData.full_name.trim().length < 2) {
      errs.full_name = 'Must be at least 2 characters.';
    }

    if (formData.email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      errs.email = 'Please enter a valid email address.';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;
    onSubmit(formData);
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-content">
        <div className="modal-header">
          <h3 className="modal-title">{isEdit ? 'Edit Student Details' : 'Register New Student'}</h3>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.25rem', color: '#64748b' }}
          >
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="form-group">
              <label className="form-label">Student ID / Roll No *</label>
              <input
                type="text"
                className="form-control"
                disabled={isEdit}
                placeholder="e.g. CS202601"
                value={formData.student_id}
                onChange={(e) => setFormData({ ...formData, student_id: e.target.value.toUpperCase() })}
              />
              {errors.student_id && <p className="form-error">{errors.student_id}</p>}
            </div>

            <div className="form-group">
              <label className="form-label">Full Name *</label>
              <input
                type="text"
                className="form-control"
                placeholder="e.g. Diya Patel"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              />
              {errors.full_name && <p className="form-error">{errors.full_name}</p>}
            </div>

            <div className="form-group">
              <label className="form-label">Department *</label>
              <select
                className="form-control"
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              >
                {DEPARTMENTS.map((dept) => (
                  <option key={dept} value={dept}>
                    {dept}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div className="form-group">
                <label className="form-label">Year of Study *</label>
                <select
                  className="form-control"
                  value={formData.year_of_study}
                  onChange={(e) => setFormData({ ...formData, year_of_study: parseInt(e.target.value, 10) })}
                >
                  <option value={1}>1st Year</option>
                  <option value={2}>2nd Year</option>
                  <option value={3}>3rd Year</option>
                  <option value={4}>4th Year</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Enrollment Status</label>
                <select
                  className="form-control"
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                >
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Email Address (Optional)</label>
              <input
                type="email"
                className="form-control"
                placeholder="student@college.edu"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              />
              {errors.email && <p className="form-error">{errors.email}</p>}
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" onClick={onClose} className="btn btn-secondary" disabled={isSubmitting}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : isEdit ? 'Update Student' : 'Register Student'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
