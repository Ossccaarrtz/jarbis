export function Skeleton({ className = "" }) {
  return <div className={`animate-pulse bg-white/[0.04] rounded-lg ${className}`} />;
}

export function CardSkeleton() {
  return (
    <div className="bg-[#0F0F18] border border-white/[0.06] rounded-xl p-4 space-y-3">
      <Skeleton className="h-3 w-1/4" />
      <Skeleton className="h-7 w-1/2" />
      <Skeleton className="h-2 w-1/3" />
    </div>
  );
}
