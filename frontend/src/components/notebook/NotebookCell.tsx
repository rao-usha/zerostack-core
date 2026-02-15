/**
 * Individual notebook cell component.
 */
import React from 'react'
import { Cell, CellResult, isPythonResult, SQLExecuteResult, PythonExecuteResult } from '../../types/notebook'
import { formatDuration, getCellTypeIcon, getCellTypeLabel, getCellPlaceholder } from '../../hooks/useNotebook'
import { styles } from './styles'
import SQLResults from './SQLResults'
import PythonResults from './PythonResults'

interface NotebookCellProps {
  cell: Cell
  index: number
  isExecuting: boolean
  hasConnection: boolean
  result?: CellResult
  isLastCell: boolean
  newCellRef?: React.RefObject<HTMLTextAreaElement>
  onUpdateContent: (content: string) => void
  onExecute: () => void
  onDelete: () => void
  onSaveAsDataset: () => void
}

export default function NotebookCell({
  cell,
  index,
  isExecuting,
  hasConnection,
  result,
  isLastCell,
  newCellRef,
  onUpdateContent,
  onExecute,
  onDelete,
  onSaveAsDataset
}: NotebookCellProps) {
  const borderColor = cell.cell_type === 'python'
    ? 'rgba(16, 185, 129, 0.3)'
    : cell.cell_type === 'sql'
      ? 'rgba(59, 130, 246, 0.3)'
      : 'rgba(255,255,255,0.1)'

  const headerBorderColor = cell.cell_type === 'python'
    ? 'rgba(16, 185, 129, 0.2)'
    : cell.cell_type === 'sql'
      ? 'rgba(59, 130, 246, 0.2)'
      : 'rgba(255,255,255,0.1)'

  const typeColor = cell.cell_type === 'python'
    ? '#10b981'
    : cell.cell_type === 'sql'
      ? '#60a5fa'
      : '#9ca3af'

  const executeButtonBg = cell.cell_type === 'python'
    ? 'rgba(16, 185, 129, 0.2)'
    : 'rgba(59, 130, 246, 0.2)'

  const executeButtonColor = cell.cell_type === 'python' ? '#10b981' : '#60a5fa'

  const isExecuteDisabled = isExecuting || (cell.cell_type === 'sql' && !hasConnection)

  return (
    <div style={{ ...styles.cell, borderColor }}>
      {/* Cell Header */}
      <div style={{ ...styles.cellHeader, borderBottomColor: headerBorderColor }}>
        <div style={styles.cellInfo}>
          <span style={{ ...styles.cellType, color: typeColor }}>
            {getCellTypeIcon(cell.cell_type)} {getCellTypeLabel(cell.cell_type)}
          </span>
          <span style={styles.cellPosition}>[{index + 1}]</span>
          {cell.last_run_status && (
            <span style={{
              ...styles.cellStatus,
              color: cell.last_run_status === 'success' ? '#10b981' :
                     cell.last_run_status === 'error' ? '#ef4444' : '#fbbf24'
            }}>
              {cell.last_run_status === 'success' ? '✓' :
               cell.last_run_status === 'error' ? '✗' : '⏳'}
              {' '}{formatDuration(cell.last_run_duration_ms)}
            </span>
          )}
        </div>
        <div style={styles.cellActions}>
          {cell.cell_type !== 'markdown' && (
            <button
              onClick={onExecute}
              disabled={isExecuteDisabled}
              style={{
                ...styles.cellActionBtn,
                backgroundColor: executeButtonBg,
                color: executeButtonColor,
                opacity: isExecuteDisabled ? 0.5 : 1
              }}
            >
              {isExecuting ? '⏳' : '▶'}
            </button>
          )}
          <button
            onClick={onDelete}
            style={{ ...styles.cellActionBtn, color: '#ef4444' }}
          >
            🗑
          </button>
        </div>
      </div>

      {/* Cell Content */}
      <textarea
        ref={isLastCell ? newCellRef : undefined}
        value={cell.content}
        onChange={(e) => onUpdateContent(e.target.value)}
        onKeyDown={(e) => {
          if (e.ctrlKey && e.key === 'Enter' && cell.cell_type !== 'markdown') {
            onExecute()
          }
        }}
        placeholder={getCellPlaceholder(cell.cell_type)}
        style={{
          ...styles.cellContent,
          fontFamily: cell.cell_type !== 'markdown' ? 'monospace' : 'inherit'
        }}
        rows={Math.max(3, cell.content.split('\n').length + 1)}
      />

      {/* Cell Results */}
      {cell.cell_type !== 'markdown' && result && (
        <div style={styles.cellResults}>
          {cell.cell_type === 'sql' && !isPythonResult(result) && (
            <SQLResults
              result={result as SQLExecuteResult}
              onSaveAsDataset={onSaveAsDataset}
            />
          )}
          {cell.cell_type === 'python' && isPythonResult(result) && (
            <PythonResults result={result as PythonExecuteResult} />
          )}
        </div>
      )}
    </div>
  )
}
