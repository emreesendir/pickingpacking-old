import styled from 'styled-components'
import { useState, useEffect } from 'react'
import Loading from '../../../global/Loading'
import Table from '../../../global/Table'
import { get, post } from '../../../global/Services'

//#region style
const Outerdiv = styled.div`
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: 95%;
`;

const Div = styled.div`
    width: 90%;
    height: 95%;
    overflow: auto;
    margin-top: 20px;
    display: flex;
    flex-direction: column;
    justify-content: top;
    border-style: solid;

    @media screen and (max-width: 700px){
        font-size: 70%;
    }
`;

const Select = styled.select`
    width: 90%;
    height: 2em;
`;

const BottomDiv = styled.div`
    width: 100%;
    height: 6%;
    display: flex;
    margin-top: auto;
    border-top: solid 0.1em;
`;

const Button = styled.button`
    width: 6em;
    margin: 0.5em 0.5em 0.5em auto;

    @media screen and (max-width: 700px){
        font-size: 70%;
    }
`;

//#endregion

//#region column setup

let changes = {};

const COLUMNS = [
    {
        Header: 'Remote Id',
        Footer: 'Remote Id',
        accessor: 'remoteId'
    },
    {
        Header: 'Order',
        Footer: 'Order',
        accessor: data => {
            return (
                <>
                    {data.productLines.map(line => 
                        <p style={{textAlign: 'left', marginLeft: '1em'}}>• {line.quantity} piece(s) {line.name}. Location: {line.location}</p>
                    )}
                </>
            )
        }
    },
    {
        Header: 'Status',
        Footer: 'Status',
        accessor: 'status'
    },
    {
        Header: 'Commands',
        Footer: 'Commands',
        accessor: data => {
            return (
                <>
                    {data.commands.split('.').map(command => 
                        <p>{command}</p>)}
                </>
            )
        }
    },
    {
        Header: 'Reason',
        Footer: 'Reason',
        accessor: 'reason'
    },
    {
        Header: 'Continue',
        Footer: 'Continue',
        accessor: data => {
            return (
                <>
                    <Select id={data.id} name="cars" onChange={(e) => changes[e.target.id] = e.target.value} defaultValue=''>
                        <option value=""></option>
                        <option value="small">Continue</option>
                    </Select>
                </>
            )
        }
    }
]

//#endregion

const OnHold = () => {
  // Table
  const [DATA, setDATA] = useState([])

  const refreshTable = () => {
      get('management/onhold/').then(data => {
          changes = {};
          setDATA([]);
          setDATA(data)
      })
  }

  useEffect(refreshTable, [])

  // Post sizes
  const [loading, setLoading] = useState([false, '', ''])

  const submit = () => {
      setLoading([true, 'Sending data to server...', 'spinner']);

      const filtered = {};
      for (const id in changes) {
          if(changes[id] !== ''){
              filtered[id] = changes[id]
          }
      }

      post('management/onhold/', filtered).then(err => {
          if(err) {
              if(err.length > 0) {
                  setLoading([true, `Error occured for some orders: ${err => JSON.stringify(err)}`, 'error']);
                  setTimeout(() => {
                      setLoading([false, '', '']);
                      refreshTable();
                  }, 2000)
              }else {
                  setLoading([true, 'Successfull.', 'done']);
                  setTimeout(() => {
                      setLoading([false, '', '']);
                      refreshTable(); 
                  }, 1000)
              }
          }else{
              setLoading([true, '! SERVER ERROR !', 'error']);
              setTimeout(() => {
                  setLoading([false, '', '']);
                  refreshTable();
              }, 1000)
          }
      })
  }

  return (
      <Outerdiv>
          {loading[0] && <Loading message={loading[1]} symbol={loading[2]}/>}
          <Div>
              <Table data={DATA} columns={COLUMNS}/>
              <BottomDiv><Button onClick={submit}>Submit</Button></BottomDiv>
          </Div>
      </Outerdiv>
  )
}

export default OnHold