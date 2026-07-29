import React from 'react';

const Card = ({ children, className = '' }) => {
  return (
    <div className={`bg-white rounded-2xl shadow-md p-4 transition-all duration-200 hover:shadow-lg ${className}`}>
      {children}
    </div>
  );
};

export default Card;
