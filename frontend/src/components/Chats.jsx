import React, { useEffect, useState } from 'react';
import axios from 'axios';
import '../style/Chatbox.css';
import '../style/ChatField.css';
import prima from '../img/primalogo.png';
import { FaUserCircle } from "react-icons/fa";
import '../style/Font.css';
import ReactMarkdown from "react-markdown";
import Loading from '../utils/Spinner';
import NoChat from './NoChat';

const Chats = () => {
  const [chats, setChats] = useState([]);
  const [error, setError] = useState('');
  const host = process.env.REACT_APP_API_HOST;
  const port = process.env.REACT_APP_API_PORT;

  useEffect(() => {
    const fetchChats = async () => {
      try {
        const response = await axios.get(`${host}:${port}/chat-history`);
        setChats(response.data.chat_history);
      } catch (err) {
        setError('Failed to fetch chat history');
        console.error(err);
      }
    };

    fetchChats();
    const intervalId = setInterval(fetchChats, 1000);
    return () => clearInterval(intervalId);
  }, [host, port]);

  return (
    <div>
      <h1 className='text-light display-6 text-center fw-bold titleApp'>Vanka-AI 2.0</h1>
      <div className={`${chats.length > 0 ? "chatfield" : ""}`}>
        {chats.length > 0 ? (
          chats.map((chat, index) => (
            <div key={index}>
              {chat.role === "user" ? (
                <div className='d-flex col-12 justify-content-end'>
                  <div className="user-message">
                    <ReactMarkdown>{chat.content}</ReactMarkdown>
                  </div>
                  <div className='d-flex align-items-center'>
                    <FaUserCircle className='text-white ms-2 px32' />
                  </div>
                </div>
              ) : (
                <div className='d-flex col-12 justify-content-start'>
                  <div className='d-flex mt-2'>
                    <img
                      style={{ width: '40px', height: '40px', marginRight: '5px' }}
                      src={prima}
                      alt="Bot"
                    />
                  </div>
                  <div className="bot-message">
                    {chat.content ? (
                    <ReactMarkdown>{chat.content}</ReactMarkdown>

                    ):(
                      <Loading />
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        ) : (
          <NoChat />
        )}
      </div>
    </div>
  );
};

export default Chats;