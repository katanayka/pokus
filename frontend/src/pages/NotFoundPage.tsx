import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold tracking-tight">Not found</h1>
      <Button asChild>
        <Link to="/catalog">Go to catalog</Link>
      </Button>
    </div>
  )
}
