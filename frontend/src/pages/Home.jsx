import React from 'react'
import Form from '../components/Form'
import Chats from '../components/Chats'
import ClearChatButton from '../components/ClearChatButton'

const Home = () => {
  return (
    <div>
        <Chats />
        <Form />
        <ClearChatButton />
    </div>
  )
}

export default Home
