export default function Logo({ className = 'h-7 w-7' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 32 32" fill="none" aria-hidden="true">
      <defs><linearGradient id="logo-g" x1="2" y1="2" x2="30" y2="30" gradientUnits="userSpaceOnUse"><stop stopColor="#22d3ee" /><stop offset="1" stopColor="#6366f1" /></linearGradient></defs>
      <rect width="32" height="32" rx="9" fill="url(#logo-g)" />
      <g stroke="#070a14" strokeWidth="2" strokeLinecap="round"><circle cx="16" cy="16" r="9.5"/><circle cx="16" cy="16" r="5"/><path d="M16 16 24 8.5"/></g><circle cx="16" cy="16" r="1.9" fill="#070a14"/><circle cx="23.6" cy="9.2" r="1.7" fill="#070a14"/>
    </svg>
  )
}
