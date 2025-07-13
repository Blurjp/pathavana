import React from 'react';
import { Price } from '../types';
import './PriceDisplay.css';

interface PriceDisplayProps {
  price: Price;
  size?: 'small' | 'medium' | 'large';
  showCurrency?: boolean;
  showChangeIndicator?: boolean;
  previousPrice?: Price;
  className?: string;
  style?: 'default' | 'prominent' | 'compact';
}

const PriceDisplay: React.FC<PriceDisplayProps> = ({
  price,
  size = 'medium',
  showCurrency = true,
  showChangeIndicator = false,
  previousPrice,
  className = '',
  style = 'default'
}) => {
  const formatPrice = (priceObj: Price): string => {
    const formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: priceObj.currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    });
    
    return formatter.format(priceObj.amount);
  };

  const calculatePriceChange = (): { amount: number; percentage: number; direction: 'up' | 'down' | 'same' } | null => {
    if (!previousPrice || previousPrice.currency !== price.currency) return null;
    
    const change = price.amount - previousPrice.amount;
    const percentage = (change / previousPrice.amount) * 100;
    
    return {
      amount: Math.abs(change),
      percentage: Math.abs(percentage),
      direction: change > 0 ? 'up' : change < 0 ? 'down' : 'same'
    };
  };

  const priceChange = showChangeIndicator ? calculatePriceChange() : null;

  return (
    <div className={`price-display ${size} ${style} ${className}`}>
      <div className="price-main">
        {style === 'compact' ? (
          <span className="amount">{price.displayPrice}</span>
        ) : (
          <>
            <span className="amount">{formatPrice(price)}</span>
            {showCurrency && price.currency !== 'USD' && (
              <span className="currency-note">({price.currency})</span>
            )}
          </>
        )}
      </div>
      
      {priceChange && priceChange.direction !== 'same' && (
        <div className={`price-change ${priceChange.direction}`}>
          <span className="change-indicator">
            {priceChange.direction === 'up' ? '↗' : '↘'}
          </span>
          <span className="change-amount">
            {formatPrice({ ...price, amount: priceChange.amount })}
          </span>
          <span className="change-percentage">
            ({priceChange.percentage.toFixed(1)}%)
          </span>
        </div>
      )}
    </div>
  );
};

export default PriceDisplay;