import React, { useState } from 'react';
import ai from '../img/Vanka-logo.png';
import axios from 'axios';
import '../style/Chatbox.css'

const NoChat = () => {
  const [prompts, setPrompts] = useState([]);
  const [selectedPrompt, setSelectedPrompt] = useState('');
  const [filteredPrompts, setFilteredPrompts] = useState([]);
  const [response, setResponse] = useState(''); // To display the API response

  const host = process.env.REACT_APP_API_HOST;                   
  const port = process.env.REACT_APP_API_PORT;  

  const fetchResponse = async (prompt) => {
    try {
      const response = await axios.post(`${host}:${port}/ask`, { question: prompt });
      setResponse(response.data.response); // Update the response state
    } catch (error) {
      console.error("Error fetching API response:", error);
      setResponse('Maaf, terjadi kesalahan saat menghubungi server.');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault(); // Prevent default form submission
    if (selectedPrompt.trim() === '') {
      alert("Please select or type a prompt before submitting.");
      return;
    }
    fetchResponse(selectedPrompt);
    setSelectedPrompt(''); // Call API with the selected prompt
  };

  // Fungsi untuk mengirim prompt otomatis
  const handleBoxClick = (prompt) => {
    setSelectedPrompt(prompt); // Set prompt yang ingin dikirim
    fetchResponse(prompt); // Kirim prompt ke API
  };

  return (
    <div className='col-12 d-flex justify-content-center align-items-center 100vh'>
      <div className="col-12 d-flex flex-column justify-content-center align-items-center">
        <img src={ai} alt="" className='vankaImg' />
        <p className="lead text-white text-center">
          Ask our AI Anything
        </p>
        <div className="col-lg-10 col-sm-12 mt-4 noChatField">
          {/* Box yang dapat diklik */}
          <div 
            onClick={() => handleBoxClick("Apa yang bisa saya tanyakan?")} 
            className='promptBox'
          >
            Apa yang bisa saya tanyakan?
          </div>
          <div 
            onClick={() => handleBoxClick("Bagaimana cara mengajukan cuti?")} 
            className='promptBox'
          >
            Bagaimana cara mengajukan cuti?
          </div>
          <div 
            onClick={() => handleBoxClick("Bagaimana cara membuat surat perjalanan dinas?")} 
            className='promptBox'
          >
            Bagaimana cara membuat surat perjalanan dinas?
          </div>
          {/* Anda bisa menambahkan lebih banyak box dengan prompt yang berbeda */}
        </div>
      </div>
    </div>
  );
}

export default NoChat;