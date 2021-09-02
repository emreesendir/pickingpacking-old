import { useState, useRef, useEffect } from 'react'
import { Link, useHistory } from 'react-router-dom'
import { checkAccessRights } from '../../global/Services'

const Dashboard = () => {
    const [accessrights, setAccessrights] = useState([]);
    const history = useRef();
    history.current = useHistory();

    useEffect(() => {
        checkAccessRights().then(access => {
            if(access) {
                if(access.includes('Modules | Dashboard')){
                    setAccessrights(access);
                }else{
                    history.current.push('/menu');
                }
            }else{
                history.current.push('/login');
            }
        })}, [])

    return (
        <div>
            <h1>Dashboard</h1>
            <Link to='/menu'><button>Menu</button></Link>
        </div>
    )
}

export default Dashboard