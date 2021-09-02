import { useState, useEffect, useRef } from 'react'
import { Link, useHistory } from 'react-router-dom'
import styled from 'styled-components'
import { checkAccessRights, get } from '../../global/Services'
import Header from './Header'
import NewPicking from './content/NewPicking'
import Loading from '../../global/Loading'

const Picking = () => {
    const [accessrights, setAccessrights] = useState([]);
    const history = useRef();
    history.current = useHistory();

    useEffect(() => {
        checkAccessRights().then(access => {
            if(access) {
                if(access.includes('Modules | Picking')){
                    setAccessrights(access);
                }else{
                    history.current.push('/menu');
                }
            }else{
                history.current.push('/login');
            }
        })}, [])

    const [pickcart, setPickcart] = useState(false)
    const [loading, setLoading] = useState([false, '', ''])

    let pickcartbarcodeInput;
    const clickPickcartbarcode = (e) => {
        e.preventDefault();
        setLoading([true, 'Retrieving data from server...', 'spinner']);
        get(`picking/pickcart/${pickcartbarcodeInput}/`).then( data => {
            if(data){
                switch(data.status) {
                    case 'AVAILABLE':
                        
                        break;
                    case 'PICKING IN PROGRESS':
                        //ask for active picking session
                        //redirect to the picking session
                        break;
                    default:
                        setLoading([true, `Invalid Status: ${data.status}`, 'error']);
                        setTimeout(() => {
                            setLoading([false, '', '']);
                            pickcartbarcodeInput = '';
                            document.getElementById('pickcartbarcode').value = '';
                            setPickcart(false);
                        }, 2000)
                  }
            }else{
                setLoading([true, '! SERVER ERROR !', 'error']);
                setTimeout(() => {
                    setLoading([false, '', '']);
                    pickcartbarcodeInput = '';
                    document.getElementById('pickcartbarcode').value = '';
                    setPickcart(false);
                }, 1000)
            }
        })
    }

    return (
        <>
            {loading[0] && <Loading message={loading[1]} symbol={loading[2]}/>}
            <div>
                <Header/>
                {!pickcart && <div>
                    <label style={{margin: '0.2em'}} htmlFor='pickcartbarcode'>SCAN or Enter PickCart Barcode</label><br/>
                    <input style={{margin: '0.2em'}}  type='text' name='pickcartbarcode' id='pickcartbarcode' onChange={e => {pickcartbarcodeInput = e.target.value}}/><br/>
                    <button style={{margin: '0.2em'}}  onClick={clickPickcartbarcode}>Continue...</button>
                </div>}
                {pickcart && {}}
            </div>
        </>
    )
}

export default Picking