import { Component, OnInit } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, Term } from 'src/app/shared/models/brick';
import { NgxSpinnerService } from 'ngx-spinner';
import { BsDatepickerConfig } from 'ngx-bootstrap/datepicker'; 

@Component({
  selector: 'app-create',
  templateUrl: './create.component.html',
  styleUrls: ['./create.component.css']
})
export class CreateComponent implements OnInit {

  constructor(
    private uploadService: UploadService,
    private spinner: NgxSpinnerService
  ) { }

  loading = false;
  successId: string;

  datepickerConfig: Partial<BsDatepickerConfig> = { containerClass: 'theme-dark-blue' };

  processData: Array<Select2OptionData> = [{id: '', text: ''}];
  campaignData: Array<Select2OptionData> = [{id: '', text: ''}];
  personnelData: Array<Select2OptionData> = [{id: '', text: ''}];

  options: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
    query: (options: Select2QueryOptions) => {
      const searchTerm = options.term;
      if (searchTerm && searchTerm.length > 3) {
        options.callback({results: []});
      } else {
          this.uploadService.searchOntTerms(searchTerm)
          .subscribe((data: any) => {
            options.callback({results: data.results as Select2OptionData});
          });
      }
    }
  };

  brick: Brick;

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
  }

  setBrickProcess(event) {
    const process = event.data[0];
    this.brick.process = new Term(process.id, process.text);
  }

  setBrickCampaign(event) {
    const campaign = event.data[0];
    this.brick.campaign = new Term(campaign.id, campaign.text);
  }

  setBrickPersonnel(event) {
    const person = event.data[0];
    this.brick.personnel = new Term(person.id, person.text);
  }

  submitBrick() {
    this.loading = true;
    this.spinner.show();
    this.uploadService.submitBrick()
      .subscribe((data: any) => {
        this.loading = false;
        this.spinner.hide();
        this.successId = data.results;
      });
  }

}
