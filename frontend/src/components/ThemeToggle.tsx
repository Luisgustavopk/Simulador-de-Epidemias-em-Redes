import { useTema } from '../hooks/useTema'
import { Icon } from './Icon'

export function ThemeToggle() {
  const { tema, alternar } = useTema()
  const rotulo = tema === 'dark' ? 'Usar tema claro' : 'Usar tema escuro'

  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={alternar}
      aria-label={rotulo}
      title={rotulo}
    >
      <Icon nome={tema === 'dark' ? 'sun' : 'moon'} size={18} />
      <span>{tema === 'dark' ? 'Tema claro' : 'Tema escuro'}</span>
    </button>
  )
}
