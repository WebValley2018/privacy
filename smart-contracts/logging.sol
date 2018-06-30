pragma solidity ^0.4.0;

contract Logging
{
    mapping (string=>uint64) timestamps;
    mapping (string=>string) events;

    function addEvent(string event_id, string ) public
    {
        users[user_id] = hash_pwd;
    }
    
    function getPwdHash(string user_id) view public returns (string)
    {
        return users[user_id];
    }
}