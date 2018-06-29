pragma solidity ^0.4.0;

contract Login
{
    int256 id;
    
    constructor() public
    {
        id = 221000;
    }
    
    function setId(int256 _id) public
    {
        id = _id;
    }
    
    function getId() view public returns (int256)
    {
        return id;
    }
}