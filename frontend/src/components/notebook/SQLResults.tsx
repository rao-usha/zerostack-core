/**
 * SQL query results table component.
 */
import { SQLExecuteResult } from '../../types/notebook'
import { formatDuration } from '../../hooks/useNotebook'
import { styles } from './styles'

interface SQLResultsProps {
  result: SQLExecuteResult
  onSaveAsDataset: () => void
}

export default function SQLResults({ result, onSaveAsDataset }: SQLResultsProps) {
  if (result.status === 'error') {
    return <div style={styles.errorResult}>❌ {result.error}</div>
  }

  if (result.status === 'running') {
    return <div style={styles.runningResult}>⏳ Running query...</div>
  }

  return (
    <>
      <div style={styles.resultHeader}>
        <span>
          ✓ {result.row_count} rows
          {result.truncated && ' (truncated)'}
          {' • '}{formatDuration(result.duration_ms)}
        </span>
        <button onClick={onSaveAsDataset} style={styles.saveDatasetBtn}>
          💾 Save as Dataset
        </button>
      </div>
      <div style={styles.resultTable}>
        <table style={styles.table}>
          <thead>
            <tr>
              {result.columns.map((col, i) => (
                <th key={i} style={styles.th}>{col.name}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.rows.slice(0, 50).map((row, i) => (
              <tr key={i} style={styles.tr}>
                {result.columns.map((col, j) => (
                  <td key={j} style={styles.td}>
                    {row[col.name] === null ? (
                      <em style={{ color: '#6b7280' }}>null</em>
                    ) : typeof row[col.name] === 'object' ? (
                      JSON.stringify(row[col.name]).slice(0, 50)
                    ) : (
                      String(row[col.name]).slice(0, 100)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {result.rows.length > 50 && (
          <div style={styles.moreRows}>... and {result.rows.length - 50} more rows</div>
        )}
      </div>
    </>
  )
}
