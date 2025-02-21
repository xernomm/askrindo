import React from 'react';
import axios from 'axios';
import '../style/Button.css';

const ClearChatButton = () => {
    const host = process.env.REACT_APP_API_HOST;
    const port = process.env.REACT_APP_API_PORT;

  const handleClearChat = async () => {
    try {
      const response = await axios.post(`${host}:${port}/truncate-chat-history`);
      console.log(response.data.message); // Show success message
    } catch (error) {
      console.error('Error clearing chat history:', error);
      alert('Failed to clear chat history.'); // Show error message
    }
  };

  return (
    <div>
      <button onClick={handleClearChat} className="btn btn-danger clear-chat-button">
        Clear Cache
      </button>
    </div>
  );
};

export default ClearChatButton;