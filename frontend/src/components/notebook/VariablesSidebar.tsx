/**
 * Session variables sidebar component.
 */
import { SessionVariable } from '../../types/notebook'
import { styles } from './styles'

interface VariablesSidebarProps {
  variables: SessionVariable[]
}

export default function VariablesSidebar({ variables }: VariablesSidebarProps) {
  if (variables.length === 0) return null

  return (
    <div style={styles.variablesSidebar}>
      <h4 style={styles.sidebarTitle}>Variables</h4>
      {variables.map((v, i) => (
        <div key={i} style={styles.variableItem}>
          <span style={styles.varName}>{v.name}</span>
          <span style={styles.varType}>{v.type}</span>
          <span style={styles.varPreview}>{v.preview}</span>
        </div>
      ))}
    </div>
  )
}
