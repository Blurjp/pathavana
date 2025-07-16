import React, { createContext, useContext, useState, ReactNode } from 'react';
import { UIState, SelectedItems } from '../types';

interface SidebarContextType extends UIState {
  toggleSidebar: () => void;
  setActiveTab: (tab: 'flights' | 'hotels' | 'activities' | 'trip') => void;
  setLoading: (loading: boolean) => void;
  toggleItemSelection: (type: 'flights' | 'hotels' | 'activities', itemId: string) => void;
  clearSelections: () => void;
  getSelectedCount: () => number;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

interface SidebarProviderProps {
  children: ReactNode;
}

export const SidebarProvider: React.FC<SidebarProviderProps> = ({ children }) => {
  const [uiState, setUiState] = useState<UIState>({
    isLoading: false,
    sidebarOpen: false,
    activeTab: 'flights',
    selectedItems: {
      flights: [],
      hotels: [],
      activities: [],
    },
  });

  const toggleSidebar = () => {
    setUiState(prev => ({
      ...prev,
      sidebarOpen: !prev.sidebarOpen,
    }));
  };

  const setActiveTab = (tab: 'flights' | 'hotels' | 'activities' | 'trip') => {
    setUiState(prev => ({
      ...prev,
      activeTab: tab as any, // Type assertion needed until UIState is updated
    }));
  };

  const setLoading = (loading: boolean) => {
    setUiState(prev => ({
      ...prev,
      isLoading: loading,
    }));
  };

  const toggleItemSelection = (
    type: 'flights' | 'hotels' | 'activities', 
    itemId: string
  ) => {
    setUiState(prev => {
      const currentSelection = prev.selectedItems[type];
      const newSelection = currentSelection.includes(itemId)
        ? currentSelection.filter(id => id !== itemId)
        : [...currentSelection, itemId];

      return {
        ...prev,
        selectedItems: {
          ...prev.selectedItems,
          [type]: newSelection,
        },
      };
    });
  };

  const clearSelections = () => {
    setUiState(prev => ({
      ...prev,
      selectedItems: {
        flights: [],
        hotels: [],
        activities: [],
      },
    }));
  };

  const getSelectedCount = (): number => {
    const { flights, hotels, activities } = uiState.selectedItems;
    return flights.length + hotels.length + activities.length;
  };

  const value: SidebarContextType = {
    ...uiState,
    toggleSidebar,
    setActiveTab,
    setLoading,
    toggleItemSelection,
    clearSelections,
    getSelectedCount,
  };

  return (
    <SidebarContext.Provider value={value}>
      {children}
    </SidebarContext.Provider>
  );
};

export const useSidebar = (): SidebarContextType => {
  const context = useContext(SidebarContext);
  if (context === undefined) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }
  return context;
};