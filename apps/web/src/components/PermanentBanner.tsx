import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
  lang: 'en' | 'hi';
}

export const PermanentBanner: React.FC<Props> = ({ lang }) => {
  return (
    <div className="bg-amber-500/15 border-b border-amber-500/30 text-amber-300 px-4 py-1.5 text-xs font-mono flex items-center justify-center gap-2 tracking-wider z-50">
      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
      <span className="font-semibold uppercase text-center">
        {lang === 'hi'
          ? "निर्णय-समर्थन अनुसंधान प्रोटोटाइप • सिमुलेशन डेटा • आधिकारिक चेतावनी प्रणाली नहीं है"
          : "DECISION SUPPORT RESEARCH PROTOTYPE • SIMULATION DATA • NOT AN OFFICIAL WARNING SYSTEM"}
      </span>
      <span className="hidden md:inline text-amber-400/70">| SIH26071</span>
    </div>
  );
};
