"use client";

import { Caveat } from "next/font/google";

const caveat = Caveat({
  subsets: ["latin"],
  weight: ["600", "700"],
  display: "swap",
});

export function StudentIllustration() {
  return (
    <div className="relative mx-auto w-full max-w-[460px] aspect-[1.1/1] select-none">
      {/* Background Bookshelf Silhouette */}
      <div className="absolute left-0 bottom-12 w-28 h-36 opacity-20 pointer-events-none">
        <svg viewBox="0 0 100 130" fill="currentColor" className="w-full h-full text-teal-300">
          <rect x="5" y="10" width="8" height="30" rx="1" />
          <rect x="15" y="5" width="10" height="35" rx="1" />
          <rect x="27" y="15" width="7" height="25" rx="1" />
          <line x1="0" y1="42" x2="90" y2="42" stroke="currentColor" strokeWidth="3" />
          <rect x="8" y="50" width="12" height="30" rx="1" />
          <rect x="22" y="45" width="8" height="35" rx="1" />
          <rect x="32" y="55" width="14" height="25" rx="1" />
          <line x1="0" y1="82" x2="90" y2="82" stroke="currentColor" strokeWidth="3" />
          {/* Wall Clock */}
          <circle cx="80" cy="20" r="12" fill="none" stroke="currentColor" strokeWidth="2" />
          <line x1="80" y1="20" x2="80" y2="13" stroke="currentColor" strokeWidth="2" />
          <line x1="80" y1="20" x2="85" y2="20" stroke="currentColor" strokeWidth="2" />
        </svg>
      </div>

      {/* Floating Card Left: AI Tutor */}
      <div className="absolute left-0 top-4 z-20 max-w-[190px] rounded-2xl border border-teal-300/20 bg-[#07302e]/85 p-3 shadow-xl backdrop-blur-md">
        <div className="flex items-start gap-2.5">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-emerald-400/20 text-emerald-300">
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="4" y="6" width="16" height="12" rx="3" />
              <circle cx="9" cy="11" r="1.5" fill="currentColor" />
              <circle cx="15" cy="11" r="1.5" fill="currentColor" />
              <path d="M9 15h6" strokeLinecap="round" />
            </svg>
          </span>
          <div>
            <p className="text-xs font-semibold text-white">AI Tutor</p>
            <p className="mt-0.5 text-[10px] leading-tight text-white/65">
              Get accurate answers from your materials.
            </p>
          </div>
        </div>
      </div>

      {/* Paper Airplane + Trajectory */}
      <div className="absolute right-4 top-2 z-10 w-24 h-16 pointer-events-none">
        <svg viewBox="0 0 100 60" fill="none" className="w-full h-full">
          <path
            d="M10 50 Q 50 10 90 20"
            stroke="#5eead4"
            strokeWidth="1.5"
            strokeDasharray="4 4"
            opacity="0.6"
          />
          <g transform="translate(82, 12) rotate(-15)">
            <path d="M0 0 L16 8 L6 10 L4 16 Z" fill="#5eead4" />
          </g>
        </svg>
      </div>

      {/* Floating Card Right: Feature Checklist */}
      <div className="absolute right-2 top-14 z-20 w-44 rounded-2xl border border-teal-300/20 bg-[#07302e]/85 p-3.5 shadow-xl backdrop-blur-md">
        <ul className="space-y-2 text-xs text-white/90">
          <li className="flex items-center gap-2.5">
            <span className="flex h-5 w-5 items-center justify-center rounded-md bg-teal-400/20 text-teal-300">
              <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
              </svg>
            </span>
            <span className="font-medium text-[11px]">Study Plan</span>
          </li>
          <li className="flex items-center gap-2.5">
            <span className="flex h-5 w-5 items-center justify-center rounded-md bg-teal-400/20 text-teal-300">
              <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="9 11 12 14 22 4" />
                <path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11" />
              </svg>
            </span>
            <span className="font-medium text-[11px]">Practice Tests</span>
          </li>
          <li className="flex items-center gap-2.5">
            <span className="flex h-5 w-5 items-center justify-center rounded-md bg-teal-400/20 text-teal-300">
              <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
            </span>
            <span className="font-medium text-[11px]">Weak Topics</span>
          </li>
          <li className="flex items-center gap-2.5">
            <span className="flex h-5 w-5 items-center justify-center rounded-md bg-teal-400/20 text-teal-300">
              <svg className="h-3 w-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <circle cx="12" cy="12" r="10" />
                <circle cx="12" cy="12" r="6" />
                <circle cx="12" cy="12" r="2" />
              </svg>
            </span>
            <span className="font-medium text-[11px]">Track Progress</span>
          </li>
        </ul>
      </div>

      {/* Floating Badge Right: Better Learning */}
      <div className="absolute right-0 bottom-24 z-20 flex items-center gap-2 rounded-xl border border-teal-300/20 bg-[#07302e]/90 px-3 py-2 shadow-lg backdrop-blur-md">
        <span className="text-teal-300">✨</span>
        <div className="text-[10px] leading-tight text-white/90">
          <p className="font-semibold text-white">Better Learning</p>
          <p className="text-teal-200/80">Brighter Future</p>
        </div>
      </div>

      {/* Script text bottom right */}
      <div className="absolute right-2 bottom-6 z-20 text-right">
        <p className={`${caveat.className} text-lg font-bold leading-tight text-[#5eead4]`}>
          Small steps
          <br />
          Big progress
        </p>
        <div className="ml-auto mt-0.5 h-0.5 w-16 rounded-full bg-[#5eead4]" />
      </div>

      {/* Main Student Vector Art Illustration */}
      <div className="absolute inset-x-0 bottom-0 top-16 flex items-end justify-center pointer-events-none">
        <svg viewBox="0 0 400 300" fill="none" className="w-full h-full max-h-[260px]">
          {/* Floor / Desk Shadow */}
          <ellipse cx="200" cy="285" rx="170" ry="10" fill="#032422" opacity="0.6" />

          {/* Plant Pot Left */}
          <g transform="translate(30, 185)">
            {/* Pot */}
            <path d="M15 60 L25 95 L55 95 L65 60 Z" fill="#14b8a6" />
            <rect x="12" y="55" width="56" height="7" rx="2" fill="#0d9488" />
            {/* Leaves */}
            <path d="M40 55 C20 40, 5 30, 10 15 C25 25, 35 40, 40 55 Z" fill="#34d399" />
            <path d="M40 55 C60 40, 75 30, 70 15 C55 25, 45 40, 40 55 Z" fill="#10b981" />
            <path d="M40 55 C30 30, 20 10, 35 0 C45 15, 42 35, 40 55 Z" fill="#059669" />
            <path d="M40 55 C50 30, 60 10, 45 0 C35 15, 38 35, 40 55 Z" fill="#34d399" />
          </g>

          {/* Chair */}
          <rect x="80" y="200" width="55" height="75" rx="10" fill="#0d9488" opacity="0.8" />
          <path d="M100 130 C75 130 75 210 100 210 L130 210 C145 210 145 130 130 130 Z" fill="#14b8a6" />

          {/* Desk */}
          <rect x="100" y="225" width="200" height="8" rx="2" fill="#0f172a" />
          <rect x="115" y="233" width="10" height="55" fill="#0f172a" />
          <rect x="275" y="233" width="10" height="55" fill="#0f172a" />

          {/* Books Stack on Desk */}
          <rect x="240" y="212" width="35" height="6" rx="1" fill="#10b981" />
          <rect x="238" y="218" width="38" height="7" rx="1" fill="#5eead4" />

          {/* Laptop */}
          <path d="M175 180 L230 180 L220 225 L165 225 Z" fill="#1e293b" />
          <path d="M178 183 L227 183 L218 222 L169 222 Z" fill="#0f172a" />
          {/* Mortarboard icon on laptop back */}
          <path transform="translate(193, 195) scale(0.6)" d="M12 3L1 9l11 6 9-4.91V17h2V9L12 3z" fill="#5eead4" />
          <rect x="155" y="225" width="75" height="3" rx="1" fill="#334155" />

          {/* Student Person */}
          {/* Hair back */}
          <path d="M105 160 C90 180 95 230 120 240 C130 240 145 200 135 160 Z" fill="#1e1b18" />

          {/* Body / Shirt */}
          <path d="M115 190 C110 230 140 250 160 250 C175 250 185 230 170 190 Z" fill="#0d9488" />

          {/* Legs / Pants */}
          <path d="M130 240 L125 280 L145 280 L150 240 Z" fill="#1e293b" />
          <path d="M150 240 L165 280 L185 280 L170 240 Z" fill="#1e293b" />
          {/* Shoes */}
          <rect x="115" y="278" width="32" height="8" rx="4" fill="#ffffff" />
          <rect x="165" y="278" width="32" height="8" rx="4" fill="#ffffff" />

          {/* Head & Face */}
          <circle cx="138" cy="155" r="18" fill="#fca5a5" />
          {/* Hair front */}
          <path d="M120 150 C120 130 155 130 155 150 C145 140 130 140 120 150 Z" fill="#1e1b18" />

          {/* Arms typing on laptop */}
          <path d="M140 195 L175 220 L165 224 L132 202 Z" fill="#fca5a5" />
        </svg>
      </div>
    </div>
  );
}

