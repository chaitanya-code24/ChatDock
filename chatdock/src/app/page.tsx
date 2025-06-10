"use client";
import { useEffect } from "react";

export default function Home() {
  // Fade-in animation for sections
  useEffect(() => {
    const sections = document.querySelectorAll(".fade-in-up");
    sections.forEach((el, i) => {
      (el as HTMLElement).style.opacity = "0";
      (el as HTMLElement).style.transform = "translateY(40px)";
      setTimeout(() => {
        (el as HTMLElement).style.transition = "all 0.7s cubic-bezier(.4,0,.2,1)";
        (el as HTMLElement).style.opacity = "1";
        (el as HTMLElement).style.transform = "translateY(0)";
      }, 150 + i * 100);
    });
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#10101a] via-[#181826] to-[#0a0a23] text-white font-sans">
      {/* Slim Glassy Navbar */}
      <nav className="fixed top-0 left-0 w-full z-50 bg-white/5 backdrop-blur-md border-b border-white/10 shadow-none">
        <div className="max-w-6xl mx-auto flex items-center justify-between px-4 sm:px-6 py-3">
          <span className="text-lg sm:text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 animate-gradient tracking-tight">
            ChatDock
          </span>
          <div className="flex gap-2 sm:gap-3 items-center text-xs sm:text-sm font-medium">
            <a href="#about" className="hover:text-blue-400 transition hidden sm:inline">About</a>
            <a href="#how" className="hover:text-blue-400 transition hidden sm:inline">How it works</a>
            <a href="#features" className="hover:text-purple-400 transition hidden sm:inline">Features</a>
            <a href="#pricing" className="hover:text-pink-400 transition hidden sm:inline">Pricing</a>
            <a
              href="#cta"
              className="bg-gradient-to-r from-blue-500 to-purple-600 px-3 sm:px-4 py-1.5 rounded-full font-semibold shadow hover:scale-105 transition text-white"
            >
              Try Free
            </a>
            <a
              href="/login"
              className="px-3 sm:px-4 py-1.5 rounded-full font-semibold bg-gradient-to-r from-pink-500 to-purple-500 text-white shadow transition-all duration-200 hover:scale-105 hover:shadow-pink-400/40 hover:bg-gradient-to-l focus:outline-none focus:ring-2 focus:ring-pink-400"
            >
              Login
            </a>
          </div>
        </div>
      </nav>

      {/* Hero + How It Works Section */}
      <section className="pt-28 sm:pt-32 pb-14 sm:pb-20 fade-in-up relative overflow-hidden">
        {/* Animated Gradient Blobs */}
        <div className="absolute -top-24 -left-24 w-[250px] sm:w-[400px] h-[250px] sm:h-[400px] bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 opacity-30 rounded-full blur-3xl animate-float pointer-events-none z-0" />
        <div className="absolute -bottom-32 right-0 w-[200px] sm:w-[350px] h-[200px] sm:h-[350px] bg-gradient-to-tr from-pink-500 via-purple-500 to-blue-500 opacity-20 rounded-full blur-2xl animate-float pointer-events-none z-0" style={{ animationDelay: "1.5s" }} />
        <div className="relative z-10 max-w-2xl sm:max-w-5xl mx-auto px-4 sm:px-6 flex flex-col items-center text-center">
          {/* Heading */}
          <h1 className="text-2xl sm:text-3xl md:text-5xl lg:text-6xl font-extrabold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 animate-gradient animate-glow leading-tight drop-shadow-lg whitespace-normal sm:whitespace-nowrap">
  Build & Embed AI Chatbots in Minutes
</h1>
          <p className="text-base sm:text-lg md:text-xl mb-8 text-gray-200 font-light animate-fade">
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-300 via-purple-300 to-pink-300 animate-gradient font-semibold">
              No coding required.
            </span>{" "}
            Train on your business content and go live instantly.
          </p>
          <button className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 sm:px-8 py-2.5 sm:py-3 rounded-full text-sm sm:text-base font-semibold shadow-lg hover:shadow-purple-500/40 transition-all hover:scale-110 animate-bounce-slow mb-10 sm:mb-12">
            🚀 Try ChatDock Free
          </button>
          {/* How It Works */}
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-center mb-8 sm:mb-10 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 animate-gradient">
            How It Works
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5 sm:gap-7 w-full">
            {[
              {
                title: "Define Your Bot",
                description: "Set your chatbot's purpose and personality.",
                icon: "🎯",
              },
              {
                title: "Train With Data",
                description: "Upload documents or connect to your content.",
                icon: "📚",
              },
              {
                title: "Go Live",
                description: "Embed on your site with one click.",
                icon: "🚀",
              },
            ].map((step, index) => (
              <div
                key={index}
                className="text-center p-5 sm:p-7 rounded-2xl bg-white/5 backdrop-blur-md shadow-lg border border-white/10 hover:border-pink-400 transition-all hover:scale-105 animate-float"
                style={{ animationDelay: `${index * 0.15}s` }}
              >
                <div className="text-3xl sm:text-4xl mb-2 sm:mb-3">{step.icon}</div>
                <h3 className="text-base sm:text-lg font-semibold mb-1 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400 animate-gradient">{step.title}</h3>
                <p className="text-gray-300 text-xs sm:text-sm">{step.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-10 sm:py-16 bg-gradient-to-b from-[#181826] to-[#10101a] fade-in-up">
        <div className="max-w-2xl sm:max-w-6xl mx-auto px-4 sm:px-6">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold text-center mb-8 sm:mb-10 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 animate-gradient">
            Features
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-7">
            {[
              "Custom Data Training",
              "One-Click Embedding",
              "No Code Required",
              "Analytics Dashboard",
              "Team Collaboration",
              "24/7 Support",
            ].map((feature, index) => (
              <div
                key={index}
                className="flex items-center p-4 sm:p-5 bg-white/5 backdrop-blur-md rounded-2xl shadow border border-white/10 hover:border-pink-400 transition-all hover:scale-105 animate-float"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="mr-2 sm:mr-3 text-pink-400">
                  <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span className="font-medium text-gray-200 text-xs sm:text-base">{feature}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-12 sm:py-20 bg-gradient-to-b from-[#10101a] to-[#181826] fade-in-up">
        <div className="max-w-2xl sm:max-w-5xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-8 sm:mb-12">
            <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-3 sm:mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 animate-gradient">
              Simple, Transparent Pricing
            </h2>
            <p className="text-gray-400 text-base sm:text-lg max-w-2xl mx-auto">
              Start building for free, then add a plan that fits your scale
            </p>
          </div>
          
          <div className="flex flex-col md:flex-row gap-6 sm:gap-8 justify-center items-stretch">
            {/* Free Plan */}
            <div className="flex-1 max-w-md bg-gradient-to-b from-white/5 to-white/10 backdrop-blur-xl rounded-2xl p-2 mx-auto">
              <div className="h-full rounded-xl p-6 sm:p-8 flex flex-col">
                <div className="mb-6 sm:mb-8">
                  <div className="flex items-center justify-between mb-3 sm:mb-4">
                    <h3 className="text-lg sm:text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
                      Free
                    </h3>
                    <span className="px-2 sm:px-3 py-1 text-xs font-semibold text-blue-400 bg-blue-400/10 rounded-full">
                      Get Started
                    </span>
                  </div>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl sm:text-4xl font-bold text-white">₹0</span>
                    <span className="text-gray-400">/month</span>
                  </div>
                </div>
                
                <ul className="space-y-3 sm:space-y-4 mb-6 sm:mb-8 flex-grow">
                  <li className="flex gap-2 sm:gap-3 items-start">
                    <svg className="w-4 h-4 sm:w-5 sm:h-5 text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                    </svg>
                    <span className="text-gray-300 text-xs sm:text-base">1 Chatbot with basic features</span>
                  </li>
                  <li className="flex gap-2 sm:gap-3 items-start">
                    <svg className="w-4 h-4 sm:w-5 sm:h-5 text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                    </svg>
                    <span className="text-gray-300 text-xs sm:text-base">50 messages per month</span>
                  </li>
                  <li className="flex gap-2 sm:gap-3 items-start">
                    <svg className="w-4 h-4 sm:w-5 sm:h-5 text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                    </svg>
                    <span className="text-gray-300 text-xs sm:text-base">Basic analytics dashboard</span>
                  </li>
                  <li className="flex gap-2 sm:gap-3 items-start">
                    <svg className="w-4 h-4 sm:w-5 sm:h-5 text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                    </svg>
                    <span className="text-gray-300 text-xs sm:text-base">Community support</span>
                  </li>
                </ul>

                <button className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg font-semibold hover:scale-105 transition-all shadow-lg hover:shadow-blue-500/25 text-xs sm:text-base">
                  Get Started Free
                </button>
              </div>
            </div>

            {/* Pro Plan */}
            <div className="flex-1 max-w-md relative mx-auto mt-8 md:mt-0">
              <div className="absolute inset-0 bg-gradient-to-b from-pink-500 to-purple-600 rounded-2xl blur-md opacity-20"></div>
              <div className="relative bg-gradient-to-b from-white/5 to-white/10 backdrop-blur-xl rounded-2xl p-2">
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-gradient-to-r from-pink-500 to-purple-500 px-3 sm:px-4 py-1 rounded-full text-xs font-bold shadow-lg">
                  Most Popular
                </div>
                <div className="h-full rounded-xl p-6 sm:p-8 flex flex-col">
                  <div className="mb-6 sm:mb-8">
                    <div className="flex items-center justify-between mb-3 sm:mb-4">
                      <h3 className="text-lg sm:text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-pink-400 to-purple-400">
                        Pro
                      </h3>
                      <span className="px-2 sm:px-3 py-1 text-xs font-semibold text-pink-400 bg-pink-400/10 rounded-full">
                        Scale Up
                      </span>
                    </div>
                    <div className="flex items-baseline gap-1">
                      <span className="text-3xl sm:text-4xl font-bold text-white">₹999</span>
                      <span className="text-gray-400">/month</span>
                    </div>
                  </div>

                  <ul className="space-y-3 sm:space-y-4 mb-6 sm:mb-8 flex-grow">
                    <li className="flex gap-2 sm:gap-3 items-start">
                      <svg className="w-4 h-4 sm:w-5 sm:h-5 text-pink-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                      </svg>
                      <span className="text-gray-300 text-xs sm:text-base">Unlimited chatbots</span>
                    </li>
                    <li className="flex gap-2 sm:gap-3 items-start">
                      <svg className="w-4 h-4 sm:w-5 sm:h-5 text-pink-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                      </svg>
                      <span className="text-gray-300 text-xs sm:text-base">10,000 messages per month</span>
                    </li>
                    <li className="flex gap-2 sm:gap-3 items-start">
                      <svg className="w-4 h-4 sm:w-5 sm:h-5 text-pink-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                      </svg>
                      <span className="text-gray-300 text-xs sm:text-base">Advanced analytics & reporting</span>
                    </li>
                    <li className="flex gap-2 sm:gap-3 items-start">
                      <svg className="w-4 h-4 sm:w-5 sm:h-5 text-pink-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                      </svg>
                      <span className="text-gray-300 text-xs sm:text-base">Priority support 24/7</span>
                    </li>
                    <li className="flex gap-2 sm:gap-3 items-start">
                      <svg className="w-4 h-4 sm:w-5 sm:h-5 text-pink-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                      </svg>
                      <span className="text-gray-300 text-xs sm:text-base">Custom branding & white label</span>
                    </li>
                    <li className="flex gap-2 sm:gap-3 items-start">
                      <svg className="w-4 h-4 sm:w-5 sm:h-5 text-pink-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"/>
                      </svg>
                      <span className="text-gray-300 text-xs sm:text-base">Team collaboration tools</span>
                    </li>
                  </ul>

                  <button className="w-full bg-gradient-to-r from-pink-500 to-purple-600 text-white px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg font-semibold hover:scale-105 transition-all shadow-lg hover:shadow-pink-500/25 text-xs sm:text-base">
                    Upgrade to Pro
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section id="cta" className="py-10 sm:py-16 fade-in-up">
        <div className="max-w-xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-5 sm:mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 animate-gradient">
            Ready to Build Your Chatbot?
          </h2>
          <button className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-6 sm:px-8 py-2.5 sm:py-3 rounded-full text-sm sm:text-base font-semibold shadow hover:shadow-purple-500/40 transition-all hover:scale-105">
            Get Started Now
          </button>
        </div>
      </section>

      {/* About Section */}
      <section id="about" className="py-12 sm:py-20 bg-gradient-to-b from-[#181826] to-[#10101a] fade-in-up">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-2xl sm:text-3xl md:text-4xl font-bold mb-5 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 animate-gradient">
            About ChatDock
          </h2>
          <p className="text-gray-300 text-base sm:text-lg mb-6">
            ChatDock empowers anyone to build, train, and deploy AI chatbots in minutes—no coding required. 
            Our mission is to make conversational AI accessible, customizable, and easy to integrate for businesses of all sizes.
          </p>
          <div className="flex flex-col sm:flex-row gap-6 justify-center mt-8">
            <div className="flex-1 bg-white/5 backdrop-blur-md rounded-xl p-6 shadow border border-white/10">
              <h3 className="font-semibold text-lg mb-2 text-blue-400">Our Vision</h3>
              <p className="text-gray-400 text-sm">
                To democratize AI-powered conversations and help every business deliver instant, smart, and engaging customer experiences.
              </p>
            </div>
            <div className="flex-1 bg-white/5 backdrop-blur-md rounded-xl p-6 shadow border border-white/10">
              <h3 className="font-semibold text-lg mb-2 text-pink-400">Why ChatDock?</h3>
              <p className="text-gray-400 text-sm">
                We focus on simplicity, security, and scalability—so you can focus on your customers, not your code.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#10101a] border-t border-white/10 py-8 mt-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-sm text-gray-400 text-center sm:text-left">
            © {new Date().getFullYear()} ChatDock. All rights reserved.
          </div>
          <div className="flex gap-4 text-gray-400 text-sm">
            <a href="#about" className="hover:text-blue-400 transition">About</a>
            <a href="#features" className="hover:text-purple-400 transition">Features</a>
            <a href="#pricing" className="hover:text-pink-400 transition">Pricing</a>
           
          </div>
        </div>
      </footer>
    </div>
  );
}
