pragma solidity ^0.4.0;

contract UserDetails
{
    mapping (string=>string) users;

    function addUser(string user_id, string hash_pwd) public
    {
        users[user_id] = hash_pwd;
    }
    
    function getPwdHash(string user_id) view public returns (string)
    {
        return users[user_id];
    }
}