interface ProgressBarProps {
  progress: number; // 0-100
  label?: string;
}

export function ProgressBar({ progress, label }: ProgressBarProps) {
  // Clamp between 0-100
  const normalizedProgress = Math.min(Math.max(progress, 0), 100);

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700">{label}</span>
          <span className="text-sm font-semibold text-blue-600">{normalizedProgress}%</span>
        </div>
      )}
      <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500 ease-out rounded-full"
          style={{ width: `${normalizedProgress}%` }}
        />
      </div>
    </div>
  );
}
