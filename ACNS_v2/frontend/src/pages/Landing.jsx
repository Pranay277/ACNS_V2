import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import acnsLogo from "../assets/acns-logo2.png";

const useCountUp = (target, duration = 1200) => {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (target === 0) { setCount(0); return; }
    let start = 0;
    const step = Math.ceil(target / (duration / 16));
    const timer = setInterval(() => {
      start += step;
      if (start >= target) { setCount(target); clearInterval(timer); }
      else setCount(start);
    }, 16);
    return () => clearInterval(timer);
  }, [target, duration]);
  return count;
};

function useReveal(stagger = 100) {
  const [visible, setVisible] = useState([]);
  const ref = useRef(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          const children = Array.from(el.children);
          children.forEach((child, i) => {
            setTimeout(() => setVisible((prev) => [...prev, i]), i * stagger);
          });
          observer.disconnect();
        }
      },
      { threshold: 0.15 }
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [stagger]);
  return { ref, visible };
}

const features = [
  {
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
    title: "Map-Based Reporting",
    description: "Pin-drop location with interactive map. Issues displayed with color-coded pins based on status.",
    color: "blue"
  },
  {
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
    ),
    title: "Auto-Routing",
    description: "Issues automatically routed to the right supervisor based on category. No manual assignment needed.",
    color: "purple"
  },
  {
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    ),
    title: "Duplicate Detection",
    description: "Smart 50m radius check prevents duplicate reports. Similar issues are flagged automatically.",
    color: "amber"
  },
  {
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    title: "Real-Time Analytics",
    description: "Live dashboard with open/resolved counts, top categories, and location hotspots.",
    color: "emerald"
  },
  {
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
    ),
    title: "Instant Notifications",
    description: "Real-time in-app notifications and email alerts for status updates and assignments.",
    color: "rose"
  },
  {
    icon: (
      <svg className="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
      </svg>
    ),
    title: "Gamification",
    description: "Earn reward points for valid reports. Leaderboard system encourages participation.",
    color: "orange"
  }
];

const steps = [
  {
    number: "01",
    title: "Report",
    description: "User captures photo, adds description & drops pin on map",
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    )
  },
  {
    number: "02",
    title: "Route",
    description: "System auto-assigns to correct supervisor instantly",
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
      </svg>
    )
  },
  {
    number: "03",
    title: "Resolve",
    description: "Supervisor fixes, uploads proof & marks as resolved",
    icon: (
      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    )
  }
];

const colorClasses = {
  blue: { bg: "bg-blue-50", text: "text-blue-600", border: "border-blue-200" },
  purple: { bg: "bg-purple-50", text: "text-purple-600", border: "border-purple-200" },
  amber: { bg: "bg-amber-50", text: "text-amber-600", border: "border-amber-200" },
  emerald: { bg: "bg-emerald-50", text: "text-emerald-600", border: "border-emerald-200" },
  rose: { bg: "bg-rose-50", text: "text-rose-600", border: "border-rose-200" },
  yellow: { bg: "bg-yellow-50", text: "text-yellow-600", border: "border-yellow-200" },
  orange: { bg: "bg-orange-50", text: "text-orange-600", border: "border-orange-200" }
};

const roleColors = {
  user: { border: "border-blue-200", hover: "hover:border-blue-300", bg: "bg-blue-50", text: "text-blue-600", light: "text-blue-500", shadow: "shadow-blue-200/50" },
  supervisor: { border: "border-purple-200", hover: "hover:border-purple-300", bg: "bg-purple-50", text: "text-purple-600", light: "text-purple-500", shadow: "shadow-purple-200/50" },
  admin: { border: "border-emerald-200", hover: "hover:border-emerald-300", bg: "bg-emerald-50", text: "text-emerald-600", light: "text-emerald-500", shadow: "shadow-emerald-200/50" }
};

const statIcons = {
  blue: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z",
  purple: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4",
  emerald: "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z",
  amber: "M13 10V3L4 14h7v7l9-11h-7z"
};

export default function Landing() {
  const navigate = useNavigate();

  const animated3 = useCountUp(3);
  const animated6 = useCountUp(6);
  const animated50 = useCountUp(50);
  const animated24 = useCountUp(24);

  const featuresReveal = useReveal(100);
  const stepsReveal = useReveal(200);
  const tryReveal = useReveal(150);

  const [featuresSectionVisible, setFeaturesSectionVisible] = useState(false);
  const [stepsSectionVisible, setStepsSectionVisible] = useState(false);
  const [trySectionVisible, setTrySectionVisible] = useState(false);

  const featuresTitleRef = useRef(null);
  const stepsTitleRef = useRef(null);
  const tryTitleRef = useRef(null);

  useEffect(() => {
    const titles = [
      { ref: featuresTitleRef, set: setFeaturesSectionVisible },
      { ref: stepsTitleRef, set: setStepsSectionVisible },
      { ref: tryTitleRef, set: setTrySectionVisible },
    ];
    titles.forEach(({ ref, set }) => {
      const el = ref.current;
      if (!el) return;
      const observer = new IntersectionObserver(
        ([entry]) => { if (entry.isIntersecting) { set(true); observer.disconnect(); } },
        { threshold: 0.3 }
      );
      observer.observe(el);
    });
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <style>{`
        @keyframes icon-bounce {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-4px); }
        }
        @keyframes pulse-glow {
          0%, 100% { box-shadow: 0 0 0 0 rgba(59,130,246,0.3); }
          50% { box-shadow: 0 0 0 8px rgba(59,130,246,0); }
        }
        @keyframes slideInUp {
          from { opacity: 0; transform: translateY(30px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes slideInLeft {
          from { opacity: 0; transform: translateX(-30px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes slideInRight {
          from { opacity: 0; transform: translateX(30px); }
          to { opacity: 1; transform: translateX(0); }
        }
        @keyframes expandCenter {
          from { width: 0; }
          to { width: 100%; }
        }
        @keyframes countPulse {
          0% { transform: scale(1); }
          50% { transform: scale(1.08); }
          100% { transform: scale(1); }
        }
        .animate-icon-bounce:hover svg { animation: icon-bounce 0.4s ease; }
        .animate-pulse-glow { animation: pulse-glow 2s ease-in-out infinite; }
      `}</style>

      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <img src={acnsLogo} alt="ACNS Logo" className="h-14 w-auto object-contain" />
            </div>
            <button
              onClick={() => navigate("/login")}
              className="px-5 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-all duration-200 hover:scale-105 hover:shadow-sm"
            >
              Get Started
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 bg-gradient-to-b from-primary-50/60 via-white to-gray-50">
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-50 rounded-full border border-primary-200 mb-8">
            <span className="w-2 h-2 bg-primary-500 rounded-full animate-pulse"></span>
            <span className="text-sm text-primary-700 font-medium">Smart Campus Issue Resolution System</span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 mb-6 leading-tight">
            Report. Track. Resolve.
            <br />
            <span className="text-primary-600">
              Transform Campus Maintenance
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-gray-500 mb-10 max-w-2xl mx-auto">
            An intelligent platform for reporting, tracking, and resolving campus issues in real-time with auto-routing and proof-based resolution.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => navigate("/login")}
              className="px-8 py-4 bg-primary-600 hover:bg-primary-700 text-white font-semibold rounded-xl transition-all duration-200 hover:scale-105 hover:shadow-lg shadow-md"
            >
              Start Reporting
            </button>
            <button
              onClick={() => document.getElementById("features").scrollIntoView({ behavior: "smooth" })}
              className="px-8 py-4 bg-white hover:bg-gray-50 border border-gray-200 text-gray-700 font-semibold rounded-xl transition-all duration-200 hover:scale-105 hover:shadow-sm"
            >
              Learn More
            </button>
          </div>
        </div>
      </section>

      {/* Stats Strip */}
      <section className="py-10 border-y border-gray-200 bg-primary-50/40">
        <div className="max-w-5xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { value: animated3, label: "User Roles", suffix: "", color: "blue" },
              { value: animated6, label: "Issue Categories", suffix: "", color: "purple" },
              { value: animated50, label: "Duplicate Detection", suffix: "m", color: "emerald" },
              { value: animated24, label: "Real-Time Updates", suffix: "/7", color: "amber" }
            ].map((stat, i) => (
              <div key={i} className="flex items-center gap-3 justify-center group">
                <div className={`w-10 h-10 flex-shrink-0 rounded-lg flex items-center justify-center transition-all duration-300 group-hover:scale-110 group-hover:shadow-md ${
                  stat.color === "blue" ? "bg-blue-100 text-blue-600" :
                  stat.color === "purple" ? "bg-purple-100 text-purple-600" :
                  stat.color === "emerald" ? "bg-emerald-100 text-emerald-600" :
                  "bg-amber-100 text-amber-600"
                }`}>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={statIcons[stat.color]} />
                  </svg>
                </div>
                <div className="text-left">
                  <div className="text-2xl font-bold text-gray-900 tabular-nums" style={{ animation: `countPulse 0.6s ease ${i * 0.15}s` }}>
                    {stat.value}{stat.suffix}
                  </div>
                  <div className="text-gray-500 text-xs">{stat.label}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <div ref={featuresTitleRef} className="text-center mb-16">
            <h2 className={`text-3xl sm:text-4xl font-bold text-gray-900 mb-4 inline-block relative transition-all duration-700 ${featuresSectionVisible ? 'opacity-100' : 'opacity-0'}`}>
              Everything You Need
              {featuresSectionVisible && (
                <span className="absolute -bottom-2 left-0 h-1 bg-primary-500 rounded-full" style={{ animation: 'expandCenter 0.6s ease forwards' }} />
              )}
            </h2>
            <p className="text-gray-500 max-w-2xl mx-auto">
              A complete solution for managing campus issues with smart automation and transparency.
            </p>
          </div>

          <div ref={featuresReveal.ref} className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, i) => (
              <div
                key={i}
                style={{ animation: featuresReveal.visible.includes(i) ? 'slideInUp 0.5s ease forwards' : 'none', opacity: featuresReveal.visible.includes(i) ? 1 : 0 }}
                className={`group bg-white rounded-xl shadow-sm border-l-4 ${colorClasses[feature.color].border} border-r border-t border-b border-gray-200 p-6 hover:shadow-xl hover:-translate-y-1 transition-all duration-300`}
              >
                <div className={`w-14 h-14 ${colorClasses[feature.color].bg} rounded-xl flex items-center justify-center mb-4 ${colorClasses[feature.color].text} transition-all duration-300 group-hover:scale-110 group-hover:shadow-md`}>
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2 group-hover:text-primary-600 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-gray-500 text-sm leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-24 px-4 bg-blue-50/30 border-y border-gray-200">
        <div className="max-w-5xl mx-auto">
          <div ref={stepsTitleRef} className="text-center mb-16">
            <h2 className={`text-3xl sm:text-4xl font-bold text-gray-900 mb-4 transition-all duration-700 ${stepsSectionVisible ? 'opacity-100' : 'opacity-0'}`}>
              How It Works
            </h2>
            <p className="text-gray-500">
              Three simple steps to a cleaner, safer campus
            </p>
          </div>

          <div ref={stepsReveal.ref} className="grid md:grid-cols-3 gap-8">
            {steps.map((step, i) => (
              <div key={i} style={{ animation: stepsReveal.visible.includes(i) ? `slideInUp 0.6s ease forwards` : 'none', opacity: stepsReveal.visible.includes(i) ? 1 : 0 }} className="relative text-center group">
                <div className="w-20 h-20 mx-auto mb-6 bg-primary-50 rounded-2xl border border-primary-200 flex items-center justify-center text-primary-600 transition-all duration-300 group-hover:scale-110 group-hover:shadow-md group-hover:bg-primary-100">
                  {step.icon}
                </div>
                <div className="text-sm font-medium text-primary-600 mb-2 group-hover:scale-105 transition-transform duration-200">{step.number}</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{step.title}</h3>
                <p className="text-gray-500 text-sm">{step.description}</p>
                {i < steps.length - 1 && (
                  <div className="hidden md:block absolute top-10 left-[calc(50%+2.5rem)] w-[calc(100%-3rem)] h-0.5 overflow-hidden -translate-y-0.5">
                    <div className="h-full bg-gradient-to-r from-primary-300 to-primary-400" style={{ transformOrigin: 'left', transition: 'transform 0.8s ease 0.3s', transform: stepsReveal.visible.includes(i) ? 'scaleX(1)' : 'scaleX(0)' }} />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Try It Out Section */}
      <section className="py-24 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <div ref={tryTitleRef}>
            <h2 className={`text-3xl sm:text-4xl font-bold text-gray-900 mb-4 transition-all duration-700 ${trySectionVisible ? 'opacity-100' : 'opacity-0'}`}>
              Try It Out
            </h2>
            <p className="text-gray-500 mb-10">
              Experience the system as different user roles
            </p>
          </div>

          <div ref={tryReveal.ref} className="grid sm:grid-cols-3 gap-4">
            {[
              { role: "user", label: "Student", desc: "Report & track issues", icon: "M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" },
              { role: "supervisor", label: "Supervisor", desc: "Manage & resolve tasks", icon: "M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" },
              { role: "admin", label: "Admin", desc: "Monitor & verify", icon: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" }
            ].map(({ role, label, desc, icon }, i) => (
              <button
                key={role}
                onClick={() => navigate("/login")}
                style={{ animation: tryReveal.visible.includes(i) ? 'slideInUp 0.5s ease forwards' : 'none', opacity: tryReveal.visible.includes(i) ? 1 : 0 }}
                className={`group p-6 bg-white rounded-xl shadow-sm border ${roleColors[role].border} ${roleColors[role].hover} hover:shadow-lg hover:-translate-y-1 transition-all duration-300`}
              >
                <div className={`w-12 h-12 mx-auto mb-4 ${roleColors[role].bg} rounded-xl flex items-center justify-center ${roleColors[role].text} transition-all duration-300 group-hover:scale-110 group-hover:rotate-3 group-hover:shadow-md`}>
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={icon} />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-1">{label}</h3>
                <p className="text-sm text-gray-500">{desc}</p>
                <span className="inline-block mt-3 text-sm font-medium transition-all duration-300 group-hover:translate-x-1" style={{ color: role === 'user' ? '#3b82f6' : role === 'supervisor' ? '#8b5cf6' : '#10b981' }}>
                  Demo Login &rarr;
                </span>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <div className="p-10 bg-gradient-to-r from-primary-600 to-indigo-600 rounded-2xl shadow-lg hover:shadow-xl transition-shadow duration-300">
            <h2 className="text-2xl sm:text-3xl font-bold text-white mb-4">
              Ready to Transform Campus Maintenance?
            </h2>
            <p className="text-primary-100 mb-8">
              Join hundreds of campuses already using SCIARS for smarter issue management.
            </p>
            <button
              onClick={() => navigate("/login")}
              className="px-8 py-4 bg-white text-primary-600 font-semibold rounded-xl transition-all duration-200 hover:scale-105 hover:shadow-lg hover:bg-gray-100"
            >
              Get Started Free
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-gray-200 bg-gray-50">
        <div className="max-w-6xl mx-auto text-center">
          <p className="text-gray-400 text-sm">
            &copy; 2024 SCIARS &mdash; Smart Campus Issue &amp; Automated Resolution System
          </p>
          <p className="text-gray-400 text-xs mt-2">
            Built for the 48-Hour Project Sprint
          </p>
        </div>
      </footer>
    </div>
  );
}
