import axios from 'axios'

const baseUrl = `http://10.13.255.185:8000/api/`;

export async function checkAccessRights() {
    try{
        const token = localStorage.getItem('token');
        let response = await axios.get(`${baseUrl}authentication/accessrights/`, {headers: {'Authorization': `Token ${token}`}})
        if(response.status === 200) {
            return response.data
        }else{
            return false
        }
    }
    catch(err) {
        console.log(err);
        return false
    }
}

export async function login(e, username, password) {
    let respone = await axios.post(`${baseUrl}authentication/token/`, { username: username, password: password })
    if(!('token' in respone.data)){
        console.log(respone.data);
        return false;
    }else{
        localStorage.setItem('token', respone.data.token);
        localStorage.setItem('username', username);
        return true;
    }
}

export async function get(endpoint) {
    try{
        const token = localStorage.getItem('token');
        let response = await axios.get(`${baseUrl}${endpoint}`, {headers: {'Authorization': `Token ${token}`}})
        if(response.status === 200) {
            return response.data
        }else{
            return false
        }
    }
    catch(err) {
        console.log(err);
        return false
    }
}

export async function post(endpoint, data) {
    try{
        const token = localStorage.getItem('token');
        let response = await axios.post(`${baseUrl}${endpoint}`, data, {headers: {'Authorization': `Token ${token}`}})
        return response.status === 200 ? response.data : false;
    }
    catch(err) {
        console.log(err);
        return false
    }
}

export async function patch(endpoint, data) {
    try{
        const token = localStorage.getItem('token');
        let response = await axios.patch(`${baseUrl}${endpoint}`, data, {headers: {'Authorization': `Token ${token}`}})
        return response.status === 200 ? response.data : false;
    }
    catch(err) {
        console.log(err);
        return false
    } 
}

export async function dlete(endpoint) {
    try{
        const token = localStorage.getItem('token');
        let response = await axios.delete(`${baseUrl}${endpoint}`, {headers: {'Authorization': `Token ${token}`}})
        return response.status === 200 ? response.data : false;
    }
    catch(err) {
        console.log(err);
        return false
    } 
}