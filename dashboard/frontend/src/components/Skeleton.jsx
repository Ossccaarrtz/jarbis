export function Skeleton({ className = "" }) {
  return (
    <div className={`animate-pulse bg-[#2A2A3A] rounded-xl ${className}`} />
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-[#1A1A24] border border-[#2A2A3A] rounded-2xl p-5 space-y-3">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}
