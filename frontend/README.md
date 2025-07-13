# Pathavana Frontend

A modern React TypeScript application for AI-powered travel planning. This frontend provides an intuitive chat interface for planning trips, finding flights and hotels, and managing travel preferences.

## Features

- **Conversational Travel Planning**: Chat-based interface for natural trip planning
- **Real-time Search Results**: Live flight, hotel, and activity search with sidebar display
- **Session Management**: Persistent chat sessions with UUID-based routing
- **Interactive Maps**: Google Maps integration for location visualization
- **Responsive Design**: Mobile-first design that works on all devices
- **TypeScript**: Full type safety throughout the application
- **Modern React**: Uses React 18 with hooks and context for state management

## Tech Stack

- **Framework**: React 18 with TypeScript
- **Routing**: React Router v6
- **State Management**: React Context + Custom Hooks
- **API Client**: Axios with interceptors
- **Styling**: CSS with CSS Variables
- **Maps**: Google Maps JavaScript API
- **Build Tool**: Create React App
- **Testing**: Jest + React Testing Library

## Project Structure

```
src/
├── components/           # Reusable UI components
│   ├── ChatInput.tsx    # Smart chat input with history
│   ├── SearchResultsSidebar.tsx # Flight/hotel results display
│   ├── FlightCard.tsx   # Individual flight option
│   ├── HotelCard.tsx    # Individual hotel option
│   ├── InteractiveMap.tsx # Map visualization
│   └── Header.tsx       # Navigation and user menu
├── pages/               # Page-level components
│   ├── TravelRequest.tsx # Main chat interface
│   ├── UnifiedTravelRequest.tsx # UUID-based session version
│   ├── Trips.tsx        # User's saved trips
│   ├── Profile.tsx      # User profile management
│   └── Travelers.tsx    # Traveler profile management
├── hooks/               # Custom React hooks
│   ├── useChatManager.ts # Chat state and history
│   ├── useSessionManager.ts # Session persistence
│   ├── useTripContext.ts # Trip planning context
│   ├── useUnifiedSession.ts # UUID-based session management
│   └── useAuth.ts       # Authentication state
├── services/            # API integration layer
│   ├── api.ts          # Main API client
│   ├── unifiedTravelApi.ts # Unified travel API
│   ├── travelApi.ts    # Legacy API endpoints
│   └── contextAPI.ts   # Context operations
├── contexts/            # React contexts
│   ├── AuthContext.tsx # Authentication state
│   └── SidebarContext.tsx # UI state management
├── types/               # TypeScript definitions
│   ├── TravelRequestTypes.ts # Core travel types
│   ├── User.ts         # User-related types
│   └── index.ts        # Type exports
├── utils/               # Utility functions
│   ├── dateHelpers.ts  # Date parsing and formatting
│   ├── sessionStorage.ts # Browser storage utilities
│   └── errorHandler.ts # Error handling utilities
└── styles/              # CSS and styling
    ├── App.css         # Main application styles
    ├── index.css       # Global utilities
    └── components/     # Component-specific styles
```

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API running (see backend README)
- Google Maps API key (optional, for map features)

### Installation

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your configuration:
   ```env
   REACT_APP_API_BASE_URL=http://localhost:8000
   REACT_APP_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   REACT_APP_ENVIRONMENT=development
   ```

3. **Start the development server**:
   ```bash
   npm start
   ```

4. **Open your browser** to [http://localhost:3000](http://localhost:3000)

### Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner in interactive watch mode
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App (irreversible)

## Key Components

### Chat Interface (`TravelRequest.tsx`)

The main chat interface where users interact with the AI travel assistant:

- Real-time messaging with typing indicators
- Message history with timestamps
- Suggestion buttons for follow-up questions
- Error handling and retry functionality

### Unified Session Management (`UnifiedTravelRequest.tsx`)

Enhanced chat interface with persistent sessions:

- UUID-based session routing (`/chat/:sessionId`)
- Context preservation across page reloads
- Interactive map integration
- Session-specific search results

### Search Results Sidebar (`SearchResultsSidebar.tsx`)

Displays and manages search results:

- Tabbed interface (Flights, Hotels, Activities)
- Selection management with local state
- Loading states and empty states
- Integration with main chat context

### Custom Hooks

#### `useUnifiedSession`
Combines chat, session, and context management:
```typescript
const {
  sessionId,
  messages,
  sendMessage,
  context,
  isLoading
} = useUnifiedSession();
```

#### `useChatManager`
Handles chat messaging and history:
```typescript
const {
  messages,
  sendMessage,
  isLoading,
  error
} = useChatManager(sessionId);
```

#### `useTripContext`
Manages travel planning context:
```typescript
const {
  context,
  updateCurrentRequest,
  addToSearchHistory
} = useTripContext(sessionId);
```

## API Integration

The frontend communicates with the backend through several API services:

### Unified Travel API (`unifiedTravelApi.ts`)
- Chat messaging: `sendChatMessage(message, sessionId)`
- Session management: `createSession()`, `getSession(id)`
- Search operations: `searchFlights()`, `searchHotels()`

### Travel API (`travelApi.ts`)
- Trip management: `getTrips()`, `createTrip()`
- Traveler profiles: `getTravelers()`, `createTraveler()`
- Booking operations: `bookFlight()`, `bookHotel()`

### Context API (`contextAPI.ts`)
- Context CRUD: `getContext()`, `updateContext()`
- Smart inference: `inferContextFromMessage()`

## State Management

The app uses a combination of React Context and custom hooks for state management:

1. **AuthContext**: User authentication and profile data
2. **SidebarContext**: UI state for search results sidebar
3. **Session Hooks**: Chat and travel planning state
4. **Local Storage**: Persistent session and preference storage

## Styling

The app uses CSS with CSS Variables for theming:

- **Design System**: Consistent colors, spacing, and typography
- **Responsive Design**: Mobile-first approach with CSS Grid/Flexbox
- **Component Styles**: Modular CSS organization
- **Dark Mode Ready**: CSS variables prepared for theme switching

## Error Handling

Comprehensive error handling throughout the application:

- **API Errors**: User-friendly messages with retry options
- **Network Errors**: Offline detection and graceful degradation
- **Validation Errors**: Form validation with helpful messages
- **Global Error Boundary**: Catches and reports React errors

## Performance Optimization

- **Code Splitting**: Dynamic imports for route-based splitting
- **API Caching**: Intelligent caching of search results
- **Debounced Inputs**: Prevents excessive API calls
- **Image Optimization**: Lazy loading and fallback images
- **Bundle Analysis**: Webpack bundle analyzer integration

## Testing

The app includes comprehensive testing setup:

- **Unit Tests**: Component and utility function tests
- **Integration Tests**: API service and hook tests
- **E2E Testing**: User journey testing (to be added)

Run tests:
```bash
npm test                # Run tests in watch mode
npm test -- --coverage # Run tests with coverage report
```

## Deployment

### Production Build

```bash
npm run build
```

This creates an optimized production build in the `build/` folder.

### Environment Variables

For production deployment, set these environment variables:

```env
REACT_APP_API_BASE_URL=https://api.pathavana.com
REACT_APP_GOOGLE_MAPS_API_KEY=your_production_api_key
REACT_APP_ENVIRONMENT=production
REACT_APP_ENABLE_ANALYTICS=true
```

### Static Hosting

The build folder can be deployed to any static hosting service:

- **Vercel**: `vercel --prod`
- **Netlify**: Drag and drop `build/` folder
- **AWS S3**: Upload `build/` contents to S3 bucket
- **Firebase Hosting**: `firebase deploy`

## Browser Support

- **Modern browsers**: Chrome 80+, Firefox 80+, Safari 13+, Edge 80+
- **Mobile browsers**: iOS Safari 13+, Chrome Mobile 80+
- **Progressive Web App**: Installable on mobile devices

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines

- Use TypeScript for all new code
- Follow the existing component structure
- Add tests for new functionality
- Update documentation as needed
- Follow the established naming conventions

## Troubleshooting

### Common Issues

1. **API Connection Errors**
   - Check if backend is running on correct port
   - Verify REACT_APP_API_BASE_URL in .env

2. **Map Not Loading**
   - Verify Google Maps API key is valid
   - Check browser console for API errors
   - Ensure API key has Maps JavaScript API enabled

3. **Build Failures**
   - Clear node_modules: `rm -rf node_modules && npm install`
   - Clear cache: `npm start -- --reset-cache`

4. **TypeScript Errors**
   - Run `npm run type-check` to see all type errors
   - Ensure all dependencies have type definitions

### Performance Issues

- Use React DevTools Profiler to identify slow components
- Check Network tab for slow API calls
- Analyze bundle size with `npm run build -- --analyze`

## Future Enhancements

- [ ] Dark mode implementation
- [ ] Offline mode with service workers
- [ ] Push notifications for trip updates
- [ ] Advanced search filters
- [ ] Trip sharing functionality
- [ ] Multi-language support
- [ ] Voice input for chat interface
- [ ] Calendar integration
- [ ] Price tracking and alerts

## License

This project is licensed under the MIT License - see the LICENSE file for details.