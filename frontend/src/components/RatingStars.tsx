import React from 'react';
import './RatingStars.css';

interface RatingStarsProps {
  rating: number;
  maxRating?: number;
  size?: 'small' | 'medium' | 'large';
  showValue?: boolean;
  showCount?: boolean;
  reviewCount?: number;
  className?: string;
  interactive?: boolean;
  onRatingChange?: (rating: number) => void;
}

const RatingStars: React.FC<RatingStarsProps> = ({
  rating,
  maxRating = 5,
  size = 'medium',
  showValue = false,
  showCount = false,
  reviewCount,
  className = '',
  interactive = false,
  onRatingChange
}) => {
  const [hoverRating, setHoverRating] = React.useState<number | null>(null);

  const handleStarClick = (starRating: number) => {
    if (interactive && onRatingChange) {
      onRatingChange(starRating);
    }
  };

  const handleStarHover = (starRating: number) => {
    if (interactive) {
      setHoverRating(starRating);
    }
  };

  const handleMouseLeave = () => {
    if (interactive) {
      setHoverRating(null);
    }
  };

  const getStarType = (starIndex: number): 'full' | 'half' | 'empty' => {
    const currentRating = hoverRating || rating;
    const starValue = starIndex + 1;
    
    if (currentRating >= starValue) {
      return 'full';
    } else if (currentRating > starIndex && currentRating < starValue) {
      return 'half';
    } else {
      return 'empty';
    }
  };

  const formatRating = (value: number): string => {
    return value % 1 === 0 ? value.toString() : value.toFixed(1);
  };

  const formatReviewCount = (count: number): string => {
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}k`;
    }
    return count.toString();
  };

  return (
    <div className={`rating-stars ${size} ${interactive ? 'interactive' : ''} ${className}`}>
      <div 
        className="stars-container"
        onMouseLeave={handleMouseLeave}
      >
        {Array.from({ length: maxRating }, (_, index) => {
          const starType = getStarType(index);
          
          return (
            <button
              key={index}
              type="button"
              className={`star ${starType}`}
              onClick={() => handleStarClick(index + 1)}
              onMouseEnter={() => handleStarHover(index + 1)}
              disabled={!interactive}
              aria-label={`Rate ${index + 1} stars`}
            >
              {starType === 'half' ? (
                <span className="star-half">
                  <span className="star-half-fill">★</span>
                  <span className="star-half-empty">☆</span>
                </span>
              ) : (
                <span className="star-icon">
                  {starType === 'full' ? '★' : '☆'}
                </span>
              )}
            </button>
          );
        })}
      </div>
      
      {(showValue || showCount) && (
        <div className="rating-details">
          {showValue && (
            <span className="rating-value">
              {formatRating(rating)}
            </span>
          )}
          
          {showCount && reviewCount !== undefined && (
            <span className="review-count">
              ({formatReviewCount(reviewCount)} review{reviewCount !== 1 ? 's' : ''})
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default RatingStars;