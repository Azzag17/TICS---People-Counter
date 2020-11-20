import { Component, OnInit } from '@angular/core';
import { CountService } from 'src/app/count.service';
import { Count } from 'src/app/count.model';

@Component({
  selector: 'app-home',
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.scss']
})

export class HomeComponent implements OnInit {
  count;

  constructor(private countService: CountService) { }

  ngOnInit(): void {
    this.countService.getCount().subscribe(data => {
      this.count = data.map(e => {
        return {
          id: e.payload.doc.id,
          data: e.payload.doc.data()
        };
      })
    });
  }
}
