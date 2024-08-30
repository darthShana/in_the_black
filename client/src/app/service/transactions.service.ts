import { Injectable } from '@angular/core';
import {Subject} from "rxjs/internal/Subject";

@Injectable({
  providedIn: 'root'
})
export class TransactionsService {

  public filterSubject: Subject<string> = new Subject();

  constructor() { }

  async confirmFilteredTransactions(option: string) {
    this.filterSubject.next(option)
  }
}
