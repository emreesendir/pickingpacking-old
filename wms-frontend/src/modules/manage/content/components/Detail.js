import styled from 'styled-components'
import { useState, useEffect, useRef } from 'react'
import { get } from '../../../../global/Services'

const Background = styled.div`

    position: absolute;
    top: 0;
    background-color: black;
    opacity: 0.2;
    height: 100%;
    width: 100%;
    z-index: 2;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;

`;

const Div = styled.div`

    position: absolute;
    z-index: 3;
    height: 75%;
    width: 75%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;

`;

const Cancel = styled.button`

    margin-left: auto;
    margin-bottom: 0.5em;
    cursor: pointer;

`;

const DetailDiv = styled.div`

    border-style: solid;
    height: 100%;
    width: 100%;
    background-color: #f0f0f0;
    color: black;
    display: grid;
    grid-template-columns: 70% 30%;
`;

const Info = styled.div`

    border-style: solid;
    overflow: hidden;
    margin: 1em 1em 1em 2em;
    user-select: text;
    display: grid;
    grid-template-columns: 50% 50%;
    grid-template-rows: 10% 10% 10% 10% 20% 40%;
    justify-items: start;
    align-items: center;

    div{
        height: 100%;
        width: 95%;
        margin: 1em;
        display: flex;
        align-items: center;
    }

    input{
        margin: 0 3em 0 auto;
    }

    label{
        margin: 0 0.5em 0 0.5em;
    }

`;

const History = styled.div`

    border-style: solid;
    margin: 1em 2em 1em 1em;
    user-select: text;
    overflow-y: auto;

    div{
        min-height: 15%;
    }

    div hr {
    
    }

`;

const Detail = ( { orderId, setStatus } ) => {

    const refContainer = useRef(orderId);
    const [DATA, setDATA] = useState(false)

    useEffect(() => {
        get(`management/detail/${refContainer.current}/`).then(data => {
            setDATA(data)
        })
    }, [])

    return (
        <>
            <Background>
            </Background>
            <Div>
                <Cancel onClick={() => setStatus(false)}>X</Cancel>
                {DATA && <DetailDiv>
                    <Info>
                        <div>
                            <label>Order ID</label>
                            <input type="text" name="id" disabled value={DATA.id}/>
                        </div>
                        <div>
                            <label>Source</label>
                            <input type="text" name="source" disabled value={DATA.source}/>
                        </div>
                        <div>
                            <label>Cache ID</label>
                            <input type="text" name="cacheId" disabled value={DATA.cacheId}/>
                        </div>
                        <div>
                            <label>Odoo Sale Order ID</label>
                            <input type="text" name="remoteId" disabled value={DATA.remoteId}/>
                        </div>
                        <div>
                            <label>Invoice Path</label>
                            <input type="text" name="invoice" disabled value={DATA.invoice}/>
                        </div>
                        <div>
                            <label>Status</label>
                            <input type="text" name="status" disabled value={DATA.status}/>
                        </div>
                        <div>
                            <label>Size</label>
                            <input type="text" name="size" disabled value={DATA.size}/>
                        </div>
                        <div>
                            <label>Commands</label>
                            <input type="text" name="commands" disabled value={DATA.commands}/>
                        </div>
                        <div style={{gridColumnStart: 'span 2', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'flex-start'}}>
                            <label>Customer Information</label>
                            <div style={{marginLeft: '0.5em', backgroundColor: '#EFEFEF4D', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'flex-start', borderColor: 'rgba(118,118,118,0.3)', borderStyle: 'solid', borderWidth: '0.1em', borderRadius: '0.2em', width: '98%'}}>
                                {DATA.shippingInformation.wk_company && <p>{DATA.shippingInformation.wk_company}</p>}
                                <p style={{margin: '0'}}>{DATA.shippingInformation.name}</p>
                                <p style={{margin: '0'}}>{DATA.shippingInformation.street}</p>
                                <p style={{margin: '0'}}>{DATA.shippingInformation.zip} {DATA.shippingInformation.city}</p>
                            </div>
                        </div>
                        <div style={{gridColumnStart: 'span 2', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'flex-start'}}>
                            <label>Order</label>
                            <div style={{marginLeft: '0.5em', backgroundColor: '#EFEFEF4D', display: 'flex', flexDirection: 'column', justifyContent: 'flex-start', alignItems: 'flex-start', borderColor: 'rgba(118,118,118,0.3)', borderStyle: 'solid', borderWidth: '0.1em', borderRadius: '0.2em', width: '98%'}}>
                            {DATA.productLines.map(line => 
                                <p style={{margin: '0'}}>• {line.quantity} piece(s) {line.name}. Location: {line.location}</p>)}
                            </div>
                        </div>
                    </Info>
                    <History>
                        {DATA.history.map(line =>
                            <div style={{ borderBottom: 'solid'}}>
                                <p style={{textAlign: 'left', marginLeft: '1em', fontSize: '70%', color: '#71afd9'}}>{line.time} - Status: {line.status}</p>
                                <p style={{textAlign: 'left', marginLeft: '0.7em'}}>{line.event}</p>
                            </div>
                        )}
                    </History>
                </DetailDiv>}
            </Div>
        </>
    )
}

export default Detail