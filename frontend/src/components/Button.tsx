import type { ButtonHTMLAttributes } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'ghost'
  size?: 'default' | 'lg'
}

export function Button({ variant = 'default', size = 'default', className = '', children, ...rest }: ButtonProps) {
  const classes = ['btn']
  if (variant === 'primary') classes.push('btn-primary')
  if (variant === 'ghost') classes.push('btn-ghost')
  if (size === 'lg') classes.push('btn-lg')
  if (className) classes.push(className)
  return (
    <button className={classes.join(' ')} {...rest}>
      {children}
    </button>
  )
}
