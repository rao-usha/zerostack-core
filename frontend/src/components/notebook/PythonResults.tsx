/**
 * Python execution results component.
 */
import { PythonExecuteResult, PythonOutput } from '../../types/notebook'
import { formatDuration } from '../../hooks/useNotebook'
import { styles } from './styles'

interface PythonResultsProps {
  result: PythonExecuteResult
}

function renderOutput(output: PythonOutput) {
  switch (output.type) {
    case 'dataframe':
      return (
        <div style={styles.dataframeOutput}>
          {output.name && <div style={styles.dfName}>{output.name}</div>}
          <div style={styles.dfShape}>
            DataFrame: {output.shape?.[0]} rows × {output.shape?.[1]} columns
            {output.truncated && ' (showing first 100)'}
          </div>
          <div style={styles.resultTable}>
            <table style={styles.table}>
              <thead>
                <tr>
                  {output.columns?.map((col, i) => (
                    <th key={i} style={styles.th}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {output.data?.slice(0, 50).map((row: any, i: number) => (
                  <tr key={i} style={styles.tr}>
                    {output.columns?.map((col, j) => (
                      <td key={j} style={styles.td}>
                        {row[col] === null ? (
                          <em style={{ color: '#6b7280' }}>null</em>
                        ) : (
                          String(row[col]).slice(0, 100)
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )

    case 'image':
      return (
        <div style={styles.imageOutput}>
          <img
            src={`data:image/${output.format || 'png'};base64,${output.data}`}
            alt="Output"
            style={{ maxWidth: '100%', borderRadius: '4px' }}
          />
        </div>
      )

    case 'text':
    default:
      return <pre style={styles.textOutput}>{output.data}</pre>
  }
}

export default function PythonResults({ result }: PythonResultsProps) {
  if (result.status === 'error') {
    return (
      <div style={styles.pythonError}>
        <div style={styles.errorResult}>❌ {result.error}</div>
        {result.traceback && (
          <pre style={styles.traceback}>{result.traceback}</pre>
        )}
      </div>
    )
  }

  if (result.status === 'running') {
    return <div style={styles.runningResult}>⏳ Executing Python...</div>
  }

  return (
    <div style={styles.pythonOutputs}>
      {/* Duration */}
      <div style={styles.pythonHeader}>
        ✓ Completed in {formatDuration(result.duration_ms)}
        {result.variables.length > 0 && (
          <span style={styles.newVars}>
            New variables: {result.variables.join(', ')}
          </span>
        )}
      </div>

      {/* Stdout */}
      {result.stdout && (
        <pre style={styles.stdout}>{result.stdout}</pre>
      )}

      {/* Stderr */}
      {result.stderr && (
        <pre style={styles.stderr}>{result.stderr}</pre>
      )}

      {/* Rich outputs */}
      {result.outputs.map((output, i) => (
        <div key={i} style={styles.outputItem}>
          {renderOutput(output)}
        </div>
      ))}

      {/* Last expression result */}
      {result.result !== null && result.result !== undefined && (
        <div style={styles.resultValue}>
          <span style={styles.resultLabel}>Out:</span>
          <span>{typeof result.result === 'object' ? JSON.stringify(result.result) : String(result.result)}</span>
        </div>
      )}
    </div>
  )
}
