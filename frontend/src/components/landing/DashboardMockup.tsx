/** Laptop dashboard mockup + floating glass cards — matches the landing reference. */
export function DashboardMockup() {
  return (
    <div className="landing-mockup relative mx-auto aspect-[5/4] w-full max-w-[540px]">
      {/* Soft desk glow */}
      <div className="absolute inset-x-8 bottom-2 h-16 rounded-full bg-teal-300/20 blur-2xl" />

      {/* Floating: AI Tutor */}
      <div className="landing-float absolute -left-2 top-[8%] z-20 max-w-[180px] rounded-xl border border-white/15 bg-[#062e2c]/80 p-3 shadow-xl backdrop-blur-md sm:-left-6 sm:max-w-[200px]">
        <div className="flex items-start gap-2.5">
          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#5eead4]/20 text-[#5eead4]">
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <rect x="5" y="8" width="14" height="10" rx="3" />
              <circle cx="9" cy="13" r="1" fill="currentColor" />
              <circle cx="15" cy="13" r="1" fill="currentColor" />
            </svg>
          </span>
          <div>
            <p className="text-xs font-semibold text-white">AI Tutor</p>
            <p className="mt-0.5 text-[10px] leading-snug text-white/65">
              Get accurate answers from your uploaded materials.
            </p>
          </div>
        </div>
      </div>

      {/* Floating: Quiz score */}
      <div className="landing-float-delay absolute -right-1 top-[22%] z-20 rounded-xl border border-white/15 bg-[#062e2c]/85 px-3 py-2.5 shadow-xl backdrop-blur-md sm:-right-4">
        <div className="flex items-center gap-2">
          <span className="text-[#5eead4]">
            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M4 19V9M10 19V5M16 19v-7" />
            </svg>
          </span>
          <div>
            <p className="text-[10px] text-white/60">Quiz Score</p>
            <p className="text-sm font-semibold text-white">82%</p>
          </div>
        </div>
        <div className="mt-2 h-1.5 w-24 overflow-hidden rounded-full bg-white/10">
          <div className="h-full w-[82%] rounded-full bg-[#5eead4]" />
        </div>
      </div>

      {/* Floating: weak topics */}
      <div className="landing-float absolute bottom-[18%] right-0 z-20 max-w-[170px] rounded-xl border border-amber-400/30 bg-[#1a2e1a]/90 px-3 py-2.5 shadow-xl backdrop-blur-md sm:-right-2">
        <div className="flex items-start gap-2">
          <span className="mt-0.5 text-amber-400">▲</span>
          <p className="text-[11px] leading-snug text-amber-100/90">
            <span className="font-semibold text-amber-200">3 weak topics.</span> Need more practice.
          </p>
        </div>
      </div>

      {/* Laptop */}
      <div className="absolute inset-x-[6%] top-[6%] bottom-[14%]">
        <div className="flex h-full flex-col overflow-hidden rounded-t-xl border border-slate-600/80 bg-[#1e293b] shadow-2xl">
          {/* Bezel top */}
          <div className="flex h-5 items-center justify-center bg-[#0f172a]">
            <span className="h-1 w-1 rounded-full bg-slate-500" />
          </div>

          {/* Screen */}
          <div className="grid min-h-0 flex-1 grid-cols-[72px_1fr] bg-[#0b1220] sm:grid-cols-[88px_1fr]">
            {/* Sidebar */}
            <aside className="border-r border-white/5 bg-[#071a1a] p-2 sm:p-2.5">
              <p className="mb-3 truncate font-serif text-[9px] font-semibold text-teal-200/90 sm:text-[10px]">
                Smart Academic
              </p>
              <ul className="space-y-1 text-[8px] text-white/50 sm:text-[9px]">
                {[
                  "Dashboard",
                  "Subjects",
                  "AI Tutor",
                  "Study Plan",
                  "Quizzes",
                  "Flashcards",
                  "Performance",
                  "Settings",
                ].map((item, i) => (
                  <li
                    key={item}
                    className={`rounded px-1.5 py-1 ${i === 0 ? "bg-[#5eead4]/15 text-[#5eead4]" : ""}`}
                  >
                    {item}
                  </li>
                ))}
              </ul>
            </aside>

            {/* Main */}
            <div className="min-w-0 space-y-2 overflow-hidden p-2.5 sm:p-3">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <p className="text-[10px] font-semibold text-white sm:text-xs">Good morning, Tirth!</p>
                  <p className="text-[8px] text-white/45">Here&apos;s your study overview</p>
                </div>
                <span className="rounded-full bg-[#5eead4]/15 px-2 py-0.5 text-[8px] font-medium text-[#5eead4]">
                  12 day streak
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg border border-white/5 bg-white/[0.03] p-2">
                  <p className="text-[8px] text-white/45">Subjects</p>
                  <ul className="mt-1 space-y-0.5 text-[8px] text-white/75">
                    <li>Machine Learning</li>
                    <li>Artificial Intelligence</li>
                    <li>SPM</li>
                  </ul>
                </div>
                <div className="rounded-lg border border-white/5 bg-white/[0.03] p-2">
                  <p className="text-[8px] text-white/45">Upcoming Exams</p>
                  <p className="mt-1 text-[9px] font-medium text-white">ML Midterm</p>
                  <p className="text-[8px] text-amber-300/90">6 days remaining</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="flex items-center gap-2 rounded-lg border border-white/5 bg-white/[0.03] p-2">
                  <div className="relative h-10 w-10 shrink-0">
                    <svg className="h-10 w-10 -rotate-90" viewBox="0 0 36 36">
                      <circle cx="18" cy="18" r="14" fill="none" stroke="#1e293b" strokeWidth="4" />
                      <circle
                        cx="18"
                        cy="18"
                        r="14"
                        fill="none"
                        stroke="#5eead4"
                        strokeWidth="4"
                        strokeDasharray="68 100"
                        strokeLinecap="round"
                      />
                    </svg>
                    <span className="absolute inset-0 flex items-center justify-center text-[8px] font-semibold text-white">
                      68%
                    </span>
                  </div>
                  <div>
                    <p className="text-[8px] text-white/45">Study Progress</p>
                    <p className="text-[9px] font-medium text-white">On track</p>
                  </div>
                </div>
                <div className="rounded-lg border border-white/5 bg-white/[0.03] p-2">
                  <p className="text-[8px] text-white/45">Weak Topics</p>
                  <p className="mt-1 text-[8px] text-rose-300">Backpropagation 44%</p>
                  <p className="text-[8px] text-amber-300">GAN 51%</p>
                </div>
              </div>

              <div className="rounded-lg border border-[#5eead4]/20 bg-[#5eead4]/5 p-2">
                <p className="text-[8px] font-semibold text-[#5eead4]">AI Tutor</p>
                <p className="mt-0.5 text-[8px] leading-snug text-white/60">
                  Explain backpropagation from my Unit 2 notes…
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Laptop base */}
        <div className="mx-auto h-2 w-[108%] -translate-x-[4%] rounded-b-md bg-gradient-to-b from-slate-600 to-slate-800" />
        <div className="mx-auto h-1.5 w-[40%] rounded-b-sm bg-slate-700" />
      </div>

      {/* Props: books + pencil */}
      <div className="absolute bottom-[2%] left-[8%] flex items-end gap-1 opacity-90">
        <div className="h-8 w-12 rounded-sm bg-[#0f766e]" />
        <div className="h-10 w-11 rounded-sm bg-[#115e59]" />
        <div className="h-7 w-10 rounded-sm bg-[#134e4a]" />
        <div className="mb-1 h-1.5 w-10 -rotate-12 rounded-full bg-emerald-400" />
      </div>

      {/* Plant */}
      <div className="absolute bottom-[4%] right-[10%] flex flex-col items-center">
        <div className="h-6 w-5 rounded-full bg-emerald-500/70 blur-[1px]" />
        <div className="h-4 w-4 rounded-sm bg-[#1e3a3a]" />
      </div>
    </div>
  );
}
