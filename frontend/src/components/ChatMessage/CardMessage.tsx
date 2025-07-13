import React from 'react';
import { CardResponse } from '../../types/AIAgentTypes';
import './CardMessage.css';

interface CardMessageProps {
  response: CardResponse;
  onAction: (action: string, data: any) => void;
}

export const CardMessage: React.FC<CardMessageProps> = ({ response, onAction }) => {
  return (
    <div className="card-message-container">
      {response.cards.map((card, index) => (
        <div key={index} className="card-item">
          {card.image && (
            <div className="card-image">
              <img src={card.image} alt={card.title} />
            </div>
          )}
          <div className="card-content">
            <h3 className="card-title">{card.title}</h3>
            <p className="card-subtitle">{card.subtitle}</p>
            
            <div className="card-details">
              {Object.entries(card.details).map(([key, value]) => (
                <div key={key} className="detail-row">
                  <span className="detail-key">{key}:</span>
                  <span className="detail-value">{value}</span>
                </div>
              ))}
            </div>
            
            <div className="card-actions">
              {card.actions.map((action, actionIndex) => (
                <button
                  key={actionIndex}
                  className={`card-action-btn ${action.action}`}
                  onClick={() => onAction(action.action, action.data)}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};