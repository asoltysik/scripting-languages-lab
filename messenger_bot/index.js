#!/usr/bin/env node
'use strict';

import BootBot from 'bootbot';
import Weather from 'weather.js';
import axios from 'axios';

const FB_PAGE_ACCESS_TOKEN = process.env.FB_PAGE_ACCESS_TOKEN;
const FB_VERIFY_TOKEN = process.env.FB_VERIFY_TOKEN;
const FB_APP_SECRET = process.env.FB_APP_SECRET;
const OPENWEATHER_KEY = process.env.OPENWEATHER_KEY;

Weather.setApiKey(OPENWEATHER_KEY);

const bot = new BootBot({
    accessToken: FB_PAGE_ACCESS_TOKEN,
    verifyToken: FB_VERIFY_TOKEN,
    appSecret: FB_APP_SECRET
});

let userInfos = {};

const getUserInfoConversation = (chat) => {
    return chat.conversation((convo) => {        
        let id = null;

        const askLocation = (convo) => convo.ask("Gdzie teraz jesteś (wpisz miejscowość)?", (answerPayload, convo) => {
            const answer = answerPayload.message.text;
            convo.set('location', answer);
            userInfos[id] = {location: answer, ...userInfos[id]};
            convo.say(`Dzięki za informację, czego chcesz się dowiedzieć? Możesz obecnie zapytać o pogodę i statystyki tego bota.`)
                .then(() => convo.end());
        });
        
        const askName = (convo) => convo.ask("Jak masz na imię?", (answerPayload, convo) => {
            const name = answerPayload.message.text;
            const lowerN = name.toLowerCase();
            if(lowerN.includes("kamil") || lowerN.includes("bart") || lowerN.includes("piotr")) {
                convo.say("Pana nie obsługujemy");
                return convo.end();
            } else {
                id = answerPayload.sender.id;
                userInfos[id] = {name: name};
                return convo.say(`Cześć, ${name}!`).then(() => askLocation(convo));
            }
        });

        return askName(convo);
    });
};

const helloCommand = {
    keywords: ['dzień dobry', 'dzien dobry', 'czesc', 'hej', 'siema'],
    handler: (payload, chat) => {
        console.log(`user said ${payload.message.text}`);
        chat.say("Cześć, na początek odpowiedz na kilka pytań.")
            .then(() => getUserInfoConversation(chat));
    }
};

const weatherCommand = {
    keywords: ['pogod'],
    handler: (payload, chat) => {
        console.log(`Handling weather request from userId ${payload.sender.id}`);

        let userInfo = userInfos[payload.sender.id];

        if(userInfo === undefined) {
            getUserInfoConversation(chat);
        } else {
            const { name, location } = userInfo;

            chat.say(`Sprawdzanie pogody w lokalizacji ${location}.`);
    
            axios.get(`https://api.openweathermap.org/data/2.5/weather?q=Kraków&appid=${OPENWEATHER_KEY}&units=metric`)
                .then(response => {
                    console.log(response);
                    chat.say(`Temperatura to ${response.data.main.temp} stopni, a odczuwalna to ${response.data.main.feels_like} stopni.`);
                });
        }
    }
}

const statsCommand = {
    keywords: ['statystyk'],
    handler: (payload, chat) => {
        chat.say(`A total of ${Object.keys(userInfos).length} have used the chatbot.`);
    }
};

const testCommand = {
    keywords: 'test',
    handler: (payload, chat) => chat.say("Test back")
};

const commands = [testCommand, helloCommand, weatherCommand, statsCommand];


commands.forEach(({keywords, handler}) => {
    bot.hear(keywords, handler);
});

bot.start();
