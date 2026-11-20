import { useEffect, useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import {
  compileLatexToPdfBlob,
  fetchDocumentVersions,
  fetchTemplates,
  renderLatexDocument,
  saveDocumentVersion,
  validateLatexCode,
} from '../services/latexService';
import type {
  DocumentVersionItem,
  TemplateItem,
} from '../types/latex';
import {
  FileText,
  Mail,
  Code2,
  Eye,
  CheckCircle2,
  AlertCircle,
  Save,
  Download,
  History,
  RefreshCw,
  Zap,
  Check,
} from 'lucide-react';

interface DocumentStudioProps {
  initialApplicationId?: number;
}

export function DocumentStudioCard({ initialApplicationId }: DocumentStudioProps) {
  const { token } = useAuth();

  const [applicationId, setApplicationId] = useState<number>(initialApplicationId || 1);
  const [docType, setDocType] = useState<'resume' | 'cover_letter'>('resume');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('modern');

  const [resumeTemplates, setResumeTemplates] = useState<TemplateItem[]>([]);
  const [coverLetterTemplates, setCoverLetterTemplates] = useState<TemplateItem[]>([]);

  // Workspace View Mode: 'split' | 'editor' | 'pdf'
  const [viewMode, setViewMode] = useState<'split' | 'editor' | 'pdf'>('split');

  const [latexCode, setLatexCode] = useState<string>('');
  const [validationStatus, setValidationStatus] = useState<{
    valid: boolean;
    message?: string | null;
  } | null>(null);

  const [pdfBlobUrl, setPdfBlobUrl] = useState<string | null>(null);
  const [versionHistory, setVersionHistory] = useState<DocumentVersionItem[]>([]);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isCompiling, setIsCompiling] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Sync prop changes
  useEffect(() => {
    if (initialApplicationId) {
      setApplicationId(initialApplicationId);
    }
  }, [initialApplicationId]);

  // Load templates on mount
  useEffect(() => {
    if (!token) return;
    fetchTemplates(token)
      .then((data) => {
        setResumeTemplates(data.resume_templates);
        setCoverLetterTemplates(data.cover_letter_templates);
      })
      .catch((err) => {
        console.error('Failed to load templates', err);
      });
  }, [token]);

  // Load versions whenever application ID or document type changes
  useEffect(() => {
    if (!token || !applicationId) return;
    loadVersions();
  }, [token, applicationId, docType]);

  const loadVersions = async () => {
    if (!token || !applicationId) return;
    try {
      const data = await fetchDocumentVersions(token, applicationId, docType);
      setVersionHistory(data.versions);
    } catch (err: any) {
      console.warn('Could not load version history:', err.message);
    }
  };

  // Render LaTeX from template
  const handleRenderDocument = async (overrideTemplate?: string) => {
    if (!token || !applicationId) return;
    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    const tmpl = overrideTemplate || selectedTemplate;

    try {
      const result = await renderLatexDocument(token, {
        application_id: applicationId,
        document_type: docType,
        template_name: tmpl,
      });
      setLatexCode(result.latex_code);
      setValidationStatus({ valid: true });
      setSuccessMessage(`Loaded ${docType === 'resume' ? 'Resume' : 'Cover Letter'} in '${tmpl}' template (v${result.version_number})`);
      await loadVersions();
      // Auto-compile preview
      compilePdfDirect(result.latex_code);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error rendering LaTeX');
    } finally {
      setIsLoading(false);
    }
  };

  const compilePdfDirect = async (code: string) => {
    if (!token || !code) return;
    setIsCompiling(true);
    try {
      const blob = await compileLatexToPdfBlob(token, code);
      const url = URL.createObjectURL(blob);
      setPdfBlobUrl(url);
    } catch (err: any) {
      console.warn('Silent compilation notice:', err.message);
    } finally {
      setIsCompiling(false);
    }
  };

  // Validate current LaTeX code
  const handleValidate = async () => {
    if (!token || !latexCode) return;
    setErrorMessage(null);
    try {
      const res = await validateLatexCode(token, latexCode);
      setValidationStatus({ valid: res.is_valid, message: res.error_message });
      if (res.is_valid) {
        setSuccessMessage('LaTeX syntax is valid and secure.');
      } else {
        setErrorMessage(res.error_message || 'Syntax error in LaTeX.');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Validation request failed');
    }
  };

  // Compile LaTeX to PDF Blob and show in embedded viewer
  const handleCompileToPdf = async () => {
    if (!token || !latexCode) return;
    setIsCompiling(true);
    setErrorMessage(null);
    try {
      const blob = await compileLatexToPdfBlob(token, latexCode);
      const url = URL.createObjectURL(blob);
      setPdfBlobUrl(url);
      setSuccessMessage('PDF compiled successfully.');
    } catch (err: any) {
      setErrorMessage(err.message || 'PDF compilation failed');
    } finally {
      setIsCompiling(false);
    }
  };

  // Download raw .tex file
  const handleDownloadTex = () => {
    if (!latexCode) return;
    const blob = new Blob([latexCode], { type: 'text/x-tex' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${docType}_app${applicationId}_${selectedTemplate}.tex`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Download compiled PDF file
  const handleDownloadPdf = async () => {
    if (!token || !latexCode) return;
    setIsCompiling(true);
    setErrorMessage(null);
    try {
      const blob = await compileLatexToPdfBlob(token, latexCode);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${docType}_app${applicationId}_${selectedTemplate}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setSuccessMessage('PDF downloaded successfully.');
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to download PDF');
    } finally {
      setIsCompiling(false);
    }
  };

  // Save current LaTeX as a new version
  const handleSaveVersion = async (isApproved = false) => {
    if (!token || !applicationId || !latexCode) return;
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const saved = await saveDocumentVersion(token, {
        application_id: applicationId,
        document_type: docType,
        template_name: selectedTemplate,
        latex_code: latexCode,
        is_approved: isApproved,
      });
      setSuccessMessage(
        `Version v${saved.version_number} saved${isApproved ? ' (Status: Approved & Finalized)' : ''}.`
      );
      await loadVersions();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save version');
    } finally {
      setIsLoading(false);
    }
  };

  // Restore past version into editor
  const handleRestoreVersion = (version: DocumentVersionItem) => {
    setLatexCode(version.latex_content);
    setSelectedTemplate(version.template_name);
    setSuccessMessage(`Restored version v${version.version_number} (${version.template_name}).`);
    setValidationStatus({ valid: true });
    compilePdfDirect(version.latex_content);
  };

  const currentTemplateList = docType === 'resume' ? resumeTemplates : coverLetterTemplates;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', maxWidth: '1240px', margin: '0 auto' }}>
      {/* Studio Top Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          paddingBottom: '1rem',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.03em', color: 'var(--text-primary)', margin: 0 }}>
            Document Studio
          </h1>
          <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', margin: '0.2rem 0 0' }}>
            Deterministic LaTeX engine, code editor, live PDF compilation, and version control.
          </p>
        </div>

        {/* Top Right Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          {/* Document Type Segmented Control */}
          <div
            style={{
              display: 'flex',
              backgroundColor: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-full)',
              padding: '2px',
            }}
          >
            <button
              type="button"
              onClick={() => {
                setDocType('resume');
                setSelectedTemplate('modern');
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.4rem 0.9rem',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
                border: 'none',
                backgroundColor: docType === 'resume' ? 'var(--pill-bg)' : 'transparent',
                color: docType === 'resume' ? 'var(--pill-text)' : 'var(--text-secondary)',
                transition: 'all 0.15s ease',
              }}
            >
              <FileText size={14} />
              <span>Tailored Resume</span>
            </button>
            <button
              type="button"
              onClick={() => {
                setDocType('cover_letter');
                setSelectedTemplate('formal');
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.4rem 0.9rem',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
                border: 'none',
                backgroundColor: docType === 'cover_letter' ? 'var(--pill-bg)' : 'transparent',
                color: docType === 'cover_letter' ? 'var(--pill-text)' : 'var(--text-secondary)',
                transition: 'all 0.15s ease',
              }}
            >
              <Mail size={14} />
              <span>Cover Letter</span>
            </button>
          </div>

          {/* Application ID Input Pill */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-full)',
              padding: '0.25rem 0.75rem',
              fontSize: '0.8125rem',
              color: 'var(--text-secondary)',
            }}
          >
            <span>App #</span>
            <input
              type="number"
              min={1}
              value={applicationId}
              onChange={(e) => setApplicationId(parseInt(e.target.value) || 1)}
              style={{
                width: '45px',
                border: 'none',
                outline: 'none',
                fontSize: '0.8125rem',
                fontWeight: 600,
                color: 'var(--text-primary)',
                backgroundColor: 'transparent',
              }}
            />
          </div>
        </div>
      </div>

      {/* Control Strip: Template Picker & Action Toolbar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '0.75rem 1rem',
        }}
      >
        {/* Template Selector Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Template:</span>
          {currentTemplateList.map((tmpl) => {
            const isSelected = selectedTemplate === tmpl.id;
            return (
              <button
                key={tmpl.id}
                type="button"
                onClick={() => {
                  setSelectedTemplate(tmpl.id);
                  handleRenderDocument(tmpl.id);
                }}
                title={tmpl.description}
                style={{
                  padding: '0.35rem 0.8rem',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.8125rem',
                  fontWeight: isSelected ? 600 : 500,
                  cursor: 'pointer',
                  border: '1px solid',
                  borderColor: isSelected ? 'var(--border-strong)' : 'var(--border-subtle)',
                  backgroundColor: isSelected ? 'var(--pill-bg)' : 'transparent',
                  color: isSelected ? 'var(--pill-text)' : 'var(--text-primary)',
                  transition: 'all 0.15s ease',
                }}
              >
                {tmpl.name}
              </button>
            );
          })}
          <button
            type="button"
            onClick={() => handleRenderDocument()}
            disabled={isLoading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.35rem 0.75rem',
              borderRadius: 'var(--radius-full)',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-subtle)',
              color: 'var(--text-primary)',
              fontSize: '0.8125rem',
              fontWeight: 500,
              cursor: isLoading ? 'not-allowed' : 'pointer',
            }}
          >
            <RefreshCw size={12} className={isLoading ? 'animate-spin' : ''} />
            <span>{isLoading ? 'Rendering...' : 'Load'}</span>
          </button>
        </div>

        {/* View Mode & Execution Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
          {/* View Mode Toggle */}
          <div
            style={{
              display: 'flex',
              backgroundColor: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-full)',
              padding: '2px',
            }}
          >
            <button
              type="button"
              onClick={() => setViewMode('split')}
              title="Side-by-side view"
              style={{
                padding: '0.3rem 0.65rem',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.75rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                backgroundColor: viewMode === 'split' ? 'var(--pill-bg)' : 'transparent',
                color: viewMode === 'split' ? 'var(--pill-text)' : 'var(--text-secondary)',
              }}
            >
              Split
            </button>
            <button
              type="button"
              onClick={() => setViewMode('editor')}
              title="Editor only"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.25rem',
                padding: '0.3rem 0.65rem',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.75rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                backgroundColor: viewMode === 'editor' ? 'var(--pill-bg)' : 'transparent',
                color: viewMode === 'editor' ? 'var(--pill-text)' : 'var(--text-secondary)',
              }}
            >
              <Code2 size={12} /> Code
            </button>
            <button
              type="button"
              onClick={() => setViewMode('pdf')}
              title="PDF only"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.25rem',
                padding: '0.3rem 0.65rem',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.75rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                backgroundColor: viewMode === 'pdf' ? 'var(--pill-bg)' : 'transparent',
                color: viewMode === 'pdf' ? 'var(--pill-text)' : 'var(--text-secondary)',
              }}
            >
              <Eye size={12} /> PDF
            </button>
          </div>

          {/* Action Buttons with Icons */}
          <button
            type="button"
            onClick={handleValidate}
            title="Validate LaTeX syntax"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.35rem 0.75rem',
              borderRadius: 'var(--radius-full)',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-surface)',
              color: 'var(--text-primary)',
              fontSize: '0.8125rem',
              fontWeight: 500,
              cursor: 'pointer',
            }}
          >
            <CheckCircle2 size={13} />
            <span>Validate</span>
          </button>

          <button
            type="button"
            onClick={handleCompileToPdf}
            disabled={isCompiling}
            className="btn-pill"
            style={{ padding: '0.4rem 0.9rem', fontSize: '0.8125rem' }}
          >
            <Zap size={13} />
            <span>{isCompiling ? 'Compiling...' : 'Compile PDF'}</span>
          </button>

          <button
            type="button"
            onClick={() => handleSaveVersion(false)}
            disabled={isLoading || !latexCode}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.35rem 0.75rem',
              borderRadius: 'var(--radius-full)',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-surface)',
              color: 'var(--text-primary)',
              fontSize: '0.8125rem',
              fontWeight: 500,
              cursor: isLoading || !latexCode ? 'not-allowed' : 'pointer',
            }}
          >
            <Save size={13} />
            <span>Save</span>
          </button>

          <button
            type="button"
            onClick={handleDownloadTex}
            disabled={!latexCode}
            title="Download .tex source code"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.35rem 0.75rem',
              borderRadius: 'var(--radius-full)',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-subtle)',
              color: 'var(--text-primary)',
              fontSize: '0.8125rem',
              fontWeight: 500,
              cursor: !latexCode ? 'not-allowed' : 'pointer',
            }}
          >
            <Download size={13} />
            <span>.tex</span>
          </button>

          <button
            type="button"
            onClick={handleDownloadPdf}
            disabled={isCompiling || !latexCode}
            title="Download compiled PDF"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.35rem 0.75rem',
              borderRadius: 'var(--radius-full)',
              border: '1px solid var(--border-subtle)',
              backgroundColor: 'var(--bg-subtle)',
              color: 'var(--text-primary)',
              fontSize: '0.8125rem',
              fontWeight: 500,
              cursor: isCompiling || !latexCode ? 'not-allowed' : 'pointer',
            }}
          >
            <Download size={13} />
            <span>PDF</span>
          </button>
        </div>
      </div>

      {/* Clean Feedback Banners */}
      {errorMessage && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.65rem 1rem',
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: 'var(--radius-md)',
            color: '#b91c1c',
            fontSize: '0.8125rem',
          }}
        >
          <AlertCircle size={15} />
          <span>{errorMessage}</span>
        </div>
      )}
      {successMessage && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.65rem 1rem',
            backgroundColor: '#f0fdf4',
            border: '1px solid #bbf7d0',
            borderRadius: 'var(--radius-md)',
            color: '#15803d',
            fontSize: '0.8125rem',
          }}
        >
          <Check size={15} />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Main Studio Viewport */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns:
            viewMode === 'split' ? '1fr 1fr' : '1fr',
          gap: '1.25rem',
          minHeight: '600px',
        }}
      >
        {/* Left Pane: LaTeX Code Editor */}
        {(viewMode === 'split' || viewMode === 'editor') && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.6rem 1rem',
                borderBottom: '1px solid var(--border-subtle)',
                backgroundColor: 'var(--bg-subtle)',
                fontSize: '0.8125rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Code2 size={14} />
                <span>LaTeX Source Code</span>
              </div>
              {validationStatus && (
                <span
                  style={{
                    fontSize: '0.75rem',
                    color: validationStatus.valid ? '#16a34a' : '#dc2626',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.3rem',
                  }}
                >
                  {validationStatus.valid ? <CheckCircle2 size={12} /> : <AlertCircle size={12} />}
                  {validationStatus.valid ? 'Valid Syntax' : 'Syntax Error'}
                </span>
              )}
            </div>

            <textarea
              value={latexCode}
              onChange={(e) => {
                setLatexCode(e.target.value);
                setValidationStatus(null);
              }}
              placeholder={`Click "Load" above to render your ${docType} into editable LaTeX source...`}
              style={{
                flex: 1,
                minHeight: '560px',
                width: '100%',
                border: 'none',
                outline: 'none',
                resize: 'none',
                padding: '1rem',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.875rem',
                lineHeight: 1.5,
                backgroundColor: '#0D0D0D',
                color: '#F8F7F3',
              }}
            />
          </div>
        )}

        {/* Right Pane: Live PDF Viewer */}
        {(viewMode === 'split' || viewMode === 'pdf') && (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
              minHeight: '600px',
            }}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.6rem 1rem',
                borderBottom: '1px solid var(--border-subtle)',
                backgroundColor: 'var(--bg-subtle)',
                fontSize: '0.8125rem',
                fontWeight: 600,
                color: 'var(--text-secondary)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Eye size={14} />
                <span>Compiled PDF Preview</span>
              </div>
              {pdfBlobUrl && (
                <button
                  type="button"
                  onClick={handleCompileToPdf}
                  title="Recompile PDF"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem',
                    border: 'none',
                    background: 'none',
                    color: 'var(--text-secondary)',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                  }}
                >
                  <RefreshCw size={11} className={isCompiling ? 'animate-spin' : ''} />
                  <span>Refresh</span>
                </button>
              )}
            </div>

            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#F2F0E8' }}>
              {pdfBlobUrl ? (
                <iframe
                  src={pdfBlobUrl}
                  title="Compiled PDF Preview"
                  style={{ width: '100%', height: '100%', minHeight: '560px', border: 'none' }}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                  <FileText size={36} style={{ color: 'var(--text-tertiary)', marginBottom: '0.75rem' }} />
                  <p style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                    No PDF preview compiled yet
                  </p>
                  <p style={{ fontSize: '0.8125rem', marginBottom: '1rem' }}>
                    Click &quot;Compile PDF&quot; or &quot;Load&quot; to build a live PDF document preview.
                  </p>
                  <button
                    type="button"
                    onClick={handleCompileToPdf}
                    disabled={isCompiling || !latexCode}
                    className="btn-pill"
                    style={{ padding: '0.45rem 1rem', fontSize: '0.8125rem' }}
                  >
                    <Zap size={13} />
                    <span>Compile Preview</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Version History Strip */}
      <div
        style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '1rem 1.25rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
          <History size={15} style={{ color: 'var(--text-secondary)' }} />
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
            Document Version History ({versionHistory.length} saved {versionHistory.length === 1 ? 'snapshot' : 'snapshots'})
          </h3>
        </div>

        {versionHistory.length === 0 ? (
          <p style={{ fontSize: '0.8125rem', color: 'var(--text-tertiary)', margin: 0 }}>
            No saved versions for Application #{applicationId} ({docType === 'resume' ? 'Resume' : 'Cover Letter'}). Click &quot;Save&quot; to create a version snapshot.
          </p>
        ) : (
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {versionHistory.map((v) => (
              <div
                key={v.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.35rem 0.75rem',
                  backgroundColor: 'var(--bg-subtle)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.8125rem',
                }}
              >
                <strong style={{ color: 'var(--text-primary)' }}>v{v.version_number}</strong>
                <span style={{ color: 'var(--text-secondary)' }}>({v.template_name})</span>
                {v.is_approved && (
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.2rem',
                      color: '#15803d',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                    }}
                  >
                    <Check size={11} /> Approved
                  </span>
                )}
                <button
                  type="button"
                  onClick={() => handleRestoreVersion(v)}
                  style={{
                    padding: '0.15rem 0.45rem',
                    borderRadius: 'var(--radius-full)',
                    border: '1px solid var(--border-subtle)',
                    backgroundColor: 'var(--bg-surface)',
                    color: 'var(--text-primary)',
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                  }}
                >
                  Load
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
