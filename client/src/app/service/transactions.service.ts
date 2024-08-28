import { Injectable } from '@angular/core';
import {Subject} from "rxjs/internal/Subject";

@Injectable({
  providedIn: 'root'
})
export class TransactionsService {

  public filterSubject: Subject<string> = new Subject();

  constructor() { }

  confirmFilteredTransactions() {
    this.filterSubject.next("flush")
  }
}
