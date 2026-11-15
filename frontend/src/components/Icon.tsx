import type { CSSProperties } from 'react'

type NomeIcone =
  | 'network'
  | 'arrow'
  | 'upload'
  | 'file'
  | 'check'
  | 'alert'
  | 'menu'
  | 'plus'
  | 'minus'
  | 'reset'
  | 'search'
  | 'chevron'
  | 'eye'
  | 'sun'
  | 'moon'
const caminhos: Record<NomeIcone, string> = {
  network: 'M12 5v5m0 4v5M5 12h5m4 0h5M7 7l3 3m4 4 3 3M7 17l3-3m4-4 3-3',
  arrow: 'M4 12h16m-6-6 6 6-6 6',
  upload: 'M12 16V3m-5 5 5-5 5 5M4 16v5h16v-5',
  file: 'M14 2H5v20h14V7l-5-5v5h5M8 12h8m-8 4h8',
  check: 'm5 12 4 4L19 6',
  alert: 'm12 3 10 18H2L12 3Zm0 6v5m0 3h.01',
  menu: 'M4 5h16M4 12h16M4 19h16M9 5v14',
  plus: 'M12 5v14M5 12h14',
  minus: 'M5 12h14',
  reset: 'M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5',
  search: 'M21 21l-5-5M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14',
  chevron: 'm8 4 8 8-8 8',
  eye: 'M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Zm10-3a3 3 0 1 0 0 6 3 3 0 0 0 0-6',
  sun: 'M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5M16 12a4 4 0 1 0-8 0 4 4 0 0 0 8 0',
  moon: 'M20.5 13a8.5 8.5 0 0 1-9.5-9.5 8.5 8.5 0 1 0 9.5 9.5Z',
}

export function Icon({
  nome,
  size = 18,
  style,
}: {
  nome: NomeIcone
  size?: number
  style?: CSSProperties
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      style={style}
    >
      <path d={caminhos[nome]} />
      {nome === 'network' && (
        <>
          <circle cx="12" cy="12" r="2" />
          <circle cx="12" cy="3" r="2" />
          <circle cx="12" cy="21" r="2" />
          <circle cx="3" cy="12" r="2" />
          <circle cx="21" cy="12" r="2" />
        </>
      )}
    </svg>
  )
}
