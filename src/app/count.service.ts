import { Injectable } from '@angular/core';
import { AngularFirestore } from '@angular/fire/firestore';
import { Observable, of as observableOf } from 'rxjs';
import { Count } from 'src/app/count.model';
import { map } from 'rxjs/operators'

@Injectable({
  providedIn: 'root'
})
export class CountService {

  constructor(private firestore: AngularFirestore) { }

  public getCount() {
    return this.firestore.collection<Count>('count_data', ref => ref.orderBy('id', 'asc')).snapshotChanges();
  }

  public getCounts() {
    return this.firestore.collection<Count>('count_data', ref => ref.orderBy('id', 'asc')).valueChanges();
  }

  public updateThreshold(new_threshold: Number) {
    return this.firestore.collection<Count>('threshold').doc('threshold_val').update({ threshold: new_threshold });
  }
}
