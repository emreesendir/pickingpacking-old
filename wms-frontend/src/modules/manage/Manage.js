import { useState, useEffect, useRef } from 'react'
import { useHistory } from 'react-router-dom'
import styled from 'styled-components'
import Navbar from './Navbar'
import Header from './Header'
import Content from './content/Content'
import { checkAccessRights } from '../../global/Services'

const Div = styled.div`
    display: grid;
    width: 100%;
    grid-template-columns: 90%;
    grid-template-rows: 1fr 1fr 25fr;
    grid-gap: 0.1em;
    justify-content: center;
    height:100%;
`;

const Manage = () => {
    const [accessrights, setAccessrights] = useState([]);
    const history = useRef();
    history.current = useHistory();

    useEffect(() => {
        checkAccessRights().then(access => {
            if(access) {
                if(access.includes('Modules | Manage')){
                    setAccessrights(access);
                }else{
                    history.current.push('/menu');
                }
            }else{
                history.current.push('/login');
            }
        })}, [])

    const [activePage, setActivePage] = useState('On Hold');

    return (
        <Div>
            <Header />
            <Navbar setActivePage={setActivePage} accessrights={accessrights}/>
            <Content activePage={activePage} accessrights={accessrights}/>
        </Div>
    )
}

export default Manage