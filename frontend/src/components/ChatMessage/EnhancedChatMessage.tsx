import React from 'react';
import { EnhancedChatMessage as ChatMessageType, CardResponse } from '../../types/AIAgentTypes';
import { CardMessage } from './CardMessage';
import './EnhancedChatMessage.css';

interface EnhancedChatMessageProps {
  message: ChatMessageType;
  onAction?: (action: string, data: any) => void;
}

export const EnhancedChatMessage: React.FC<EnhancedChatMessageProps> = ({ 
  message, 
  onAction 
}) => {
  const formatTimestamp = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: 'numeric',
      minute: 'numeric',
      hour12: true
    }).format(date);
  };

  const renderContent = () => {
    // Check if the content is a card response
    if (message.metadata.attachments) {
      const cardAttachment = message.metadata.attachments.find(
        att => att.type === 'card'
      );
      if (cardAttachment && cardAttachment.metadata) {
        return (
          <CardMessage 
            response={cardAttachment.metadata as CardResponse} 
            onAction={onAction || (() => {})}
          />
        );
      }
    }

    // Check if content has markdown formatting
    if (message.content.includes('**') || message.content.includes('##')) {
      return (
        <div 
          className="message-content markdown"
          dangerouslySetInnerHTML={{ __html: formatMarkdown(message.content) }}
        />
      );
    }

    // Regular text content
    return <div className="message-content">{message.content}</div>;
  };

  const formatMarkdown = (text: string) => {
    // Simple markdown parsing
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/## (.*?)$/gm, '<h3>$1</h3>')
      .replace(/### (.*?)$/gm, '<h4>$1</h4>')
      .replace(/\n/g, '<br />');
  };

  const renderMetadata = () => {
    const { intent, entities } = message.metadata;

    return (
      <div className="message-metadata">
        {intent && (
          <div className="intent-badge">
            <span className="badge-label">Intent:</span>
            <span className="badge-value">{intent.type}</span>
            <span className="confidence">({Math.round(intent.confidence * 100)}%)</span>
          </div>
        )}
        
        {entities && entities.length > 0 && (
          <div className="entities-list">
            <span className="entities-label">Detected:</span>
            {entities.map((entity, index) => (
              <span key={index} className="entity-chip">
                {entity.type}: {entity.value}
              </span>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`enhanced-chat-message ${message.role}`}>
      <div className="message-header">
        <span className="message-role">
          {message.role === 'user' ? '👤' : message.role === 'agent' ? '🤖' : '⚙️'}
        </span>
        <span className="message-time">{formatTimestamp(message.timestamp)}</span>
      </div>
      
      {renderContent()}
      
      {message.role === 'user' && message.metadata && renderMetadata()}
      
      {message.metadata.suggestions && message.metadata.suggestions.length > 0 && (
        <div className="suggestions">
          <span className="suggestions-label">Suggestions:</span>
          <div className="suggestions-list">
            {message.metadata.suggestions.map((suggestion, index) => (
              <button
                key={index}
                className="suggestion-chip"
                onClick={() => onAction?.('suggestion', suggestion)}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}
      
      {message.metadata.actionRequired && (
        <div className="action-required">
          <span className="action-icon">⚠️</span>
          <span className="action-text">Action required</span>
        </div>
      )}
    </div>
  );
};