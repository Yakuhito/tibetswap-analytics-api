from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import desc, func, BigInteger
from cachetools import cached, TTLCache
from sqlalchemy.orm import Session
from typing import List
import models, database
import os

app = APIRouter()
cache = TTLCache(maxsize=100, ttl=10)

# Dependency for getting DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@cached(cache)
@app.get("/router")
async def get_router(db: Session = Depends(get_db)):
    router = db.query(models.Router).first()
    return router

@cached(cache)
@app.get("/pairs")
async def get_pairs(db: Session = Depends(get_db)):
    return await _get_pairs(db)

async def _get_pairs(db: Session):
    pairs = db.query(models.Pair).all()
    return pairs

@cached(cache)
@app.get("/pair/{pair_launcher_id}")
async def get_pair(pair_launcher_id: str, db: Session = Depends(get_db)):
    pair = db.query(models.Pair).filter(models.Pair.launcher_id == pair_launcher_id).first()
    if pair is None:
        raise HTTPException(status_code=404, detail="Pair not found")
    return pair

@cached(cache)
@app.get("/transactions/{pair_launcher_id}")
async def get_transactions(pair_launcher_id: str, limit: int = 42, offset: int = 0, db: Session = Depends(get_db)):
    transactions = (
        db.query(models.Transaction)
        .filter(models.Transaction.pair_launcher_id == pair_launcher_id)
        .order_by(desc(models.Transaction.height))
        .limit(limit)
        .offset(offset)
        .all()
    )
    return transactions

@cached(cache)
@app.get("/transactions")
async def get_transactions(limit: int = 42, offset: int = 0, db: Session = Depends(get_db)):
    transactions = (
        db.query(models.Transaction)
        .order_by(desc(models.Transaction.height))
        .limit(limit)
        .offset(offset)
        .all()
    )
    return transactions

@cached(cache)
@app.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    # Number of transactions
    transaction_count = db.query(func.count(models.Transaction.coin_id)).scalar()

    # Total value locked (two times the sum of all Pairs' xch_reserve)
    total_value_locked = (
        db.query(func.sum(models.Pair.xch_reserve)).scalar() or 0
    ) * 2

    # Total trade volume (sum of all Pairs' trade_volume, converted from string to int)
    total_trade_volume = (
        db.query(func.sum(func.cast(models.Pair.trade_volume, BigInteger))).scalar() or 0
    )

    return {
        "transaction_count": transaction_count,
        "total_value_locked": total_value_locked,
        "total_trade_volume": total_trade_volume,
    }

@app.get("/")
async def root():
    return {"message": "TibetSwap Analytics API is running"}