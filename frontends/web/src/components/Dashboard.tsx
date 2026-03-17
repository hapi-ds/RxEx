/**
 * Dashboard Component
 * Central hub with action cards for Save/Read/Clear, AI Skills, and Graph Editor.
 *
 * **Validates: Requirements 1.1, 2.1–2.4, 3.1–3.6, 4.1–4.6, 8.1–8.6, 12.1–12.5, 14.1–14.8, 16.1–16.4**
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { dataAPI, skillsAPI, mindsAPI, fmeaAPI } from '../services/api';
import type { SaveFileData } from '../types';
import type { Mind } from '../types/generated';
import './Dashboard.css';

export function Dashboard(): JSX.Element {
  const navigate = useNavigate();

  // Save/Read/Clear state
  const [saveLoading, setSaveLoading] = useState(false);
  const [readLoading, setReadLoading] = useState(false);
  const [clearLoading, setClearLoading] = useState(false);
  const [dataMessage, setDataMessage] = useState<string | null>(null);
  const [dataError, setDataError] = useState<string | null>(null);

  // Skills card state
  const [enabledCount, setEnabledCount] = useState<number | null>(null);
  const [skillsError, setSkillsError] = useState(false);

  // Project cards state
  const [projects, setProjects] = useState<Mind[]>([]);
  const [selectedClassicProject, setSelectedClassicProject] = useState('');
  const [selectedAgileProject, setSelectedAgileProject] = useState('');

  // FMEA card state
  const [fmeaLoading, setFmeaLoading] = useState<string | null>(null);
  const [fmeaError, setFmeaError] = useState<string | null>(null);

  const loadSkillCount = useCallback(async (): Promise<void> => {
    try {
      const skills = await skillsAPI.list();
      setEnabledCount(skills.filter((s) => s.enabled).length);
      setSkillsError(false);
    } catch {
      setSkillsError(true);
    }
  }, []);

  const loadProjects = useCallback(async (): Promise<void> => {
    try {
      const allMinds = await mindsAPI.list();
      const projectMinds = allMinds.filter(m => {
        const raw = m as unknown as Record<string, unknown>;
        const mt = String(raw.mind_type ?? raw.__primarylabel__ ?? '').toLowerCase();
        return mt === 'project';
      });
      setProjects(projectMinds);
      if (projectMinds.length > 0) {
        const firstUuid = String(projectMinds[0].uuid);
        setSelectedClassicProject(firstUuid);
        setSelectedAgileProject(firstUuid);
      }
    } catch {
      // silently fail — cards will show "no projects"
    }
  }, []);

  useEffect(() => {
    loadSkillCount();
    loadProjects();
  }, [loadSkillCount, loadProjects]);

  const handleSave = async (): Promise<void> => {
    setSaveLoading(true);
    setDataMessage(null);
    setDataError(null);
    try {
      const data = await dataAPI.save();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const a = document.createElement('a');
      a.href = url;
      a.download = `generated-data-${timestamp}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setDataMessage('Data saved successfully.');
    } catch (err) {
      setDataError(err instanceof Error ? err.message : 'Failed to save data');
    } finally {
      setSaveLoading(false);
    }
  };

  const handleRead = (): void => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e: Event): Promise<void> => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      setReadLoading(true);
      setDataMessage(null);
      setDataError(null);
      try {
        const text = await file.text();
        const parsed: SaveFileData = JSON.parse(text);
        const result = await dataAPI.read(parsed);
        setDataMessage(
          `Read complete: ${result.minds_count} minds, ${result.relationships_count} relationships, ${result.posts_count} posts restored.`
        );
      } catch (err) {
        setDataError(err instanceof Error ? err.message : 'Failed to read data');
      } finally {
        setReadLoading(false);
      }
    };
    input.click();
  };

  const handleClear = async (): Promise<void> => {
    if (!confirm('Are you sure you want to clear all Generated Data? This cannot be undone. Users and Skills will be preserved.')) {
      return;
    }
    setClearLoading(true);
    setDataMessage(null);
    setDataError(null);
    try {
      const result = await dataAPI.clear();
      setDataMessage(
        `Cleared: ${result.minds_deleted} minds, ${result.relationships_deleted} relationships, ${result.posts_deleted} posts deleted.`
      );
    } catch (err) {
      setDataError(err instanceof Error ? err.message : 'Failed to clear data');
    } finally {
      setClearLoading(false);
    }
  };

  const isDataBusy = saveLoading || readLoading || clearLoading;

  const handleFmeaDownload = async (fmeaType: string, label: string): Promise<void> => {
    setFmeaLoading(fmeaType);
    setFmeaError(null);
    try {
      const blob = await fmeaAPI.downloadReport(fmeaType);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `fmea_report_${fmeaType}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      if (err instanceof Error) {
        if (err.message.includes('404')) {
          setFmeaError('No FMEA data available. Load example data first.');
        } else if (err.message.includes('400')) {
          setFmeaError('Invalid report type.');
        } else if (err.message.includes('500')) {
          setFmeaError('Report generation failed. Please try again.');
        } else {
          setFmeaError(err.message || 'Network error. Check your connection.');
        }
      } else {
        setFmeaError('Network error. Check your connection.');
      }
    } finally {
      setFmeaLoading(null);
    }
  };

  const isFmeaBusy = fmeaLoading !== null;

  return (
    <div className="dashboard-container">
      <h2>Dashboard</h2>
      <div className="dashboard-grid">
        {/* Save / Read / Clear card */}
        <section className="dashboard-card">
          <h3>Save / Read</h3>
          <p>Export, import, or clear all generated data (minds, relationships, posts).</p>
          <div className="card-actions">
            <button onClick={handleSave} disabled={isDataBusy} className="btn-primary">
              {saveLoading ? 'Saving…' : 'Save'}
            </button>
            <button onClick={handleRead} disabled={isDataBusy} className="btn-primary">
              {readLoading ? 'Reading…' : 'Read'}
            </button>
            <button onClick={handleClear} disabled={isDataBusy} className="btn-danger">
              {clearLoading ? 'Clearing…' : 'Clear DB'}
            </button>
          </div>
          {dataMessage && <p className="card-success">{dataMessage}</p>}
          {dataError && <p className="card-error">{dataError}</p>}
        </section>

        {/* AI Skills card */}
        <section className="dashboard-card">
          <h3>AI Skills</h3>
          <p>Manage knowledge and rules for the AI.</p>
          {skillsError ? (
            <p className="card-error">Skills unavailable</p>
          ) : (
            enabledCount !== null && (
              <p className="card-info">{enabledCount} skill{enabledCount !== 1 ? 's' : ''} enabled</p>
            )
          )}
          <div className="card-actions">
            <button onClick={() => navigate('/skills')} className="btn-primary">
              Manage Skills
            </button>
          </div>
        </section>

        {/* Graph Editor card */}
        <section className="dashboard-card">
          <h3>Graph Editor</h3>
          <p>Visualize and edit the knowledge graph.</p>
          <div className="card-actions">
            <button onClick={() => navigate('/graph-editor')} className="btn-primary">
              Open Graph Editor
            </button>
          </div>
        </section>

        {/* Classic Project View card */}
        <section className="dashboard-card">
          <h3>Classic Project View</h3>
          <p>Gantt chart, critical path, and schedule management.</p>
          {projects.length === 0 ? (
            <p className="card-info">No projects available</p>
          ) : (
            <label>
              Project:{' '}
              <select
                value={selectedClassicProject}
                onChange={e => setSelectedClassicProject(e.target.value)}
              >
                {projects.map(p => (
                  <option key={String(p.uuid)} value={String(p.uuid)}>{p.title}</option>
                ))}
              </select>
            </label>
          )}
          <div className="card-actions">
            <button
              onClick={() => navigate(`/project-classic/${selectedClassicProject}`)}
              disabled={!selectedClassicProject}
              className="btn-primary"
            >
              Open Classic View
            </button>
          </div>
        </section>

        {/* Agile Project View card */}
        <section className="dashboard-card">
          <h3>Agile Project View</h3>
          <p>Sprint board, burn-down chart, and backlog management.</p>
          {projects.length === 0 ? (
            <p className="card-info">No projects available</p>
          ) : (
            <label>
              Project:{' '}
              <select
                value={selectedAgileProject}
                onChange={e => setSelectedAgileProject(e.target.value)}
              >
                {projects.map(p => (
                  <option key={String(p.uuid)} value={String(p.uuid)}>{p.title}</option>
                ))}
              </select>
            </label>
          )}
          <div className="card-actions">
            <button
              onClick={() => navigate(`/project-agile/${selectedAgileProject}`)}
              disabled={!selectedAgileProject}
              className="btn-primary"
            >
              Open Agile View
            </button>
          </div>
        </section>

        {/* FMEA Risk Analysis card */}
        <section className="dashboard-card">
          <h3>FMEA Risk Analysis</h3>
          <p>Download Failure Mode and Effects Analysis reports as XLSX files.</p>
          <div className="card-actions">
            <button
              onClick={() => handleFmeaDownload('design', 'Design FMEA')}
              disabled={isFmeaBusy}
              className="btn-primary"
            >
              {fmeaLoading === 'design' ? 'Downloading…' : 'Design FMEA'}
            </button>
            <button
              onClick={() => handleFmeaDownload('process', 'Process FMEA')}
              disabled={isFmeaBusy}
              className="btn-primary"
            >
              {fmeaLoading === 'process' ? 'Downloading…' : 'Process FMEA'}
            </button>
            <button
              onClick={() => handleFmeaDownload('iso14971', 'ISO 14971')}
              disabled={isFmeaBusy}
              className="btn-primary"
            >
              {fmeaLoading === 'iso14971' ? 'Downloading…' : 'ISO 14971'}
            </button>
            <button
              onClick={() => handleFmeaDownload('general', 'General FMEA')}
              disabled={isFmeaBusy}
              className="btn-primary"
            >
              {fmeaLoading === 'general' ? 'Downloading…' : 'General FMEA'}
            </button>
          </div>
          {fmeaError && <p className="card-error">{fmeaError}</p>}
        </section>
      </div>
    </div>
  );
}
