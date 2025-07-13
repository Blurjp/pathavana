import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { LoginModal } from '../components/auth/LoginModalSimple';
import { 
  Plane, 
  Hotel, 
  MapPin, 
  Calendar, 
  Users, 
  Sparkles,
  Globe,
  Shield,
  Clock,
  ChevronRight,
  Star,
  Zap
} from 'lucide-react';

const Landing: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);

  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate('/chat');
    } else {
      setShowLoginModal(true);
    }
  };

  const handleLoginSuccess = () => {
    setShowLoginModal(false);
    navigate('/chat');
  };

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="container">
          <div className="hero-content">
            <h1 className="hero-title">
              Plan Your Perfect Trip with
              <span className="text-primary"> AI-Powered Intelligence</span>
            </h1>
            <p className="hero-subtitle">
              Let Pathavana's AI assistant help you discover amazing destinations, 
              find the best flights and hotels, and create unforgettable travel experiences.
            </p>
            <div className="hero-actions">
              <button 
                onClick={handleGetStarted}
                className="btn-primary btn-large"
              >
                Start Planning Your Trip
                <ChevronRight className="ml-2 h-5 w-5" />
              </button>
              <button 
                onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                className="btn-secondary btn-large"
              >
                Learn More
              </button>
            </div>
            <div className="hero-stats">
              <div className="stat">
                <Star className="h-5 w-5 text-yellow-500" />
                <span>50,000+ Happy Travelers</span>
              </div>
              <div className="stat">
                <Globe className="h-5 w-5 text-primary" />
                <span>200+ Destinations</span>
              </div>
              <div className="stat">
                <Zap className="h-5 w-5 text-green-500" />
                <span>AI-Powered Planning</span>
              </div>
            </div>
          </div>
          <div className="hero-image">
            <div className="hero-visual">
              <Globe className="h-64 w-64 text-primary opacity-20 animate-pulse" />
              <div className="floating-cards">
                <div className="card flight">
                  <Plane className="h-8 w-8" />
                  <span>Flights</span>
                </div>
                <div className="card hotel">
                  <Hotel className="h-8 w-8" />
                  <span>Hotels</span>
                </div>
                <div className="card activity">
                  <MapPin className="h-8 w-8" />
                  <span>Activities</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="features-section">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Everything You Need for Perfect Travel Planning</h2>
            <p className="section-subtitle">
              Our AI assistant understands your preferences and helps you create personalized travel experiences
            </p>
          </div>
          
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">
                <Sparkles className="h-8 w-8" />
              </div>
              <h3>AI-Powered Recommendations</h3>
              <p>
                Get personalized suggestions based on your preferences, budget, and travel style. 
                Our AI learns what you love.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <Plane className="h-8 w-8" />
              </div>
              <h3>Smart Flight Search</h3>
              <p>
                Find the best flights with flexible dates, multiple airlines, and real-time pricing. 
                Compare options instantly.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <Hotel className="h-8 w-8" />
              </div>
              <h3>Perfect Accommodations</h3>
              <p>
                Discover hotels that match your style and budget. From luxury resorts to cozy boutiques, 
                we've got you covered.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <MapPin className="h-8 w-8" />
              </div>
              <h3>Local Activities</h3>
              <p>
                Explore authentic experiences and must-see attractions. Our AI suggests activities 
                based on your interests.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <Calendar className="h-8 w-8" />
              </div>
              <h3>Smart Itineraries</h3>
              <p>
                Get day-by-day itineraries optimized for your pace. We handle the logistics so you 
                can enjoy the journey.
              </p>
            </div>

            <div className="feature-card">
              <div className="feature-icon">
                <Users className="h-8 w-8" />
              </div>
              <h3>Group Planning</h3>
              <p>
                Planning with friends or family? Collaborate on trips and find options that work 
                for everyone.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works-section">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">How It Works</h2>
            <p className="section-subtitle">
              Start planning your dream trip in just three simple steps
            </p>
          </div>
          
          <div className="steps">
            <div className="step">
              <div className="step-number">1</div>
              <h3>Tell Us Your Dreams</h3>
              <p>
                Share your destination ideas, travel dates, and preferences. 
                Our AI understands natural language - just chat!
              </p>
            </div>
            
            <div className="step">
              <div className="step-number">2</div>
              <h3>Get Personalized Options</h3>
              <p>
                Receive curated flights, hotels, and activities tailored to your needs. 
                Compare and choose what excites you.
              </p>
            </div>
            
            <div className="step">
              <div className="step-number">3</div>
              <h3>Book with Confidence</h3>
              <p>
                Save your favorite options and book when ready. 
                We'll keep track of everything for a stress-free experience.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Trust Section */}
      <section className="trust-section">
        <div className="container">
          <div className="trust-grid">
            <div className="trust-item">
              <Shield className="h-12 w-12 text-primary mb-4" />
              <h3>Secure & Private</h3>
              <p>Your data is encrypted and never shared. Travel planning with peace of mind.</p>
            </div>
            
            <div className="trust-item">
              <Clock className="h-12 w-12 text-primary mb-4" />
              <h3>24/7 AI Assistant</h3>
              <p>Get help anytime, anywhere. Our AI is always ready to assist with your travel needs.</p>
            </div>
            
            <div className="trust-item">
              <Star className="h-12 w-12 text-primary mb-4" />
              <h3>Trusted by Thousands</h3>
              <p>Join travelers who've discovered smarter trip planning with Pathavana.</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-content">
            <h2>Ready to Start Your Adventure?</h2>
            <p>Join thousands of travelers who plan smarter with Pathavana</p>
            <button 
              onClick={handleGetStarted}
              className="btn-primary btn-large"
            >
              Start Planning for Free
              <ChevronRight className="ml-2 h-5 w-5" />
            </button>
          </div>
        </div>
      </section>

      {/* Login Modal */}
      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onSuccess={handleLoginSuccess}
      />
    </div>
  );
};

export default Landing;