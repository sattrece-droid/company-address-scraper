interface AdPlaceholderProps {
  size?: "banner" | "sidebar" | "interstitial";
  className?: string;
}

export function AdPlaceholder({ size = "banner", className = "" }: AdPlaceholderProps) {
  const sizes = {
    banner: "w-full h-[90px]",
    sidebar: "w-[300px] h-[600px]",
    interstitial: "w-full h-screen",
  };

  return (
    <div
      className={`${sizes[size]} bg-gray-200 border-2 border-gray-300 rounded-lg flex items-center justify-center text-gray-600 ${className}`}
    >
      {process.env.NEXT_PUBLIC_ADSENSE_ID ? (
        // Real AdSense slot (placeholder for now)
        <div className="text-center text-sm">
          <p className="font-semibold">Advertisement</p>
          <p className="text-xs text-gray-500">(Google AdSense)</p>
        </div>
      ) : (
        // Development placeholder
        <div className="text-center text-sm">
          <p className="font-semibold">Ad Placeholder</p>
          <p className="text-xs text-gray-500">
            {size === "banner" && "728×90"}
            {size === "sidebar" && "300×600"}
            {size === "interstitial" && "Full Screen"}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Add NEXT_PUBLIC_ADSENSE_ID to .env to show real ads
          </p>
        </div>
      )}
    </div>
  );
}
