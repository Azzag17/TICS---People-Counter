import { Component, OnInit, OnDestroy } from '@angular/core';
import { CountService } from 'src/app/count.service';
import { Count } from 'src/app/count.model';


@Component({
  selector: 'app-graph',
  templateUrl: './graph.component.html',
  styleUrls: ['./graph.component.scss']
})

export class GraphComponent implements OnInit, OnDestroy {
  count: Count[] = [];
  options: any;

  constructor(private countService: CountService) {}

  ngOnInit(): void {
    this.countService.getCounts().subscribe(data => {
      this.count = data;

      var count_data = [];
      var threshold = [];
      var xTime = [];

      for (var c of this.count) {
        count_data.push(c.count);
        threshold.push(c.threshold);

        let d = new Date(c.time['seconds']*1000);

        let day = d.getDate();
        let month = d.getMonth();
        let year = d.getFullYear();
        let hour = d.getHours();
        let mins = d.getMinutes();

        //hour + ": " + mins + " " + day + "/" + month + "/" + year

        xTime.push(day + "/" + month + "/" + year);
      }   

      console.log(count_data);
      console.log(threshold);
      console.log(xTime)

      this.options = {
        legend: {
          data: ['count', 'threshold'],
          align: 'left'
        },
        tooltip: {},
        xAxis: {
          data: xTime,
          silent: false,
          splitline: {
            show: false,
          },
        },
        yAxis: {},
        series: [
          {
            name: 'count',
            type: 'line',
            data: count_data,
            animationDelay: (idx) => idx * 10,
          },
          {
            name: 'threshold',
            type: 'line',
            data: threshold,
            animationDelay: (idx) => idx * 10,
          },
        ],
        animationEasing: 'elasticOut',
        animationDelayUpdate: (idx) => idx * 5,
      };
    });
  }

  ngOnDestroy() {
    console.log("Destroyed lad");
    this.countService.getCounts().subscribe().unsubscribe();
  }

  addThreshold(newThreshold: number) {
    this.countService.updateThreshold(newThreshold);
    console.log("Threshold updated to " + newThreshold);
  }

}
