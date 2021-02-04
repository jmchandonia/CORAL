import { async, ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { HttpClientModule } from '@angular/common/http';
import { PreviewComponent } from './preview.component';
import { ModalModule } from 'ngx-bootstrap/modal';
import { RouterModule } from '@angular/router';
import { Brick, DataValue, TypedProperty, Term, BrickDimension } from 'src/app/shared/models/brick';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Subject, of } from 'rxjs';
import { BrickFactoryService } from 'src/app/shared/services/brick-factory.service';
import{ Router } from '@angular/router';
const metadata = require('src/app/shared/test/brick-type-templates.json');
import { By } from '@angular/platform-browser';

describe('PreviewComponent', () => {

  let brick: Brick = BrickFactoryService.createUploadInstance(metadata.results[0].children[1]);
  let mockCoreObjectRefs = [
    {
    var_name: 'Environmental Sample ID',
    count: 100
  },
  {
    var_name: 'Other Test Object Ref',
    count: 50
  }
];

  const MockUploadService = {
    getBrickBuilder: () => brick,
    getRefsToCoreObjects: () => of({
      results: mockCoreObjectRefs
    })
  };

  const MockRouter = {
    navigate: () => {}
  }

  let spectator: Spectator<PreviewComponent>;
  const createComponent = createComponentFactory({
    component: PreviewComponent,
    imports: [
      HttpClientModule,
      ModalModule.forRoot(),
      RouterModule.forRoot([])
    ],
    providers: [
      mockProvider(UploadService, MockUploadService),
      mockProvider(Router, MockRouter)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should have instance of brick builder', () => {
    expect(spectator.component.brick).not.toBeUndefined();
    expect(spectator.component.brick instanceof Brick).toBeTruthy();
  });

  it('should render meta info', () => {
    const cardTitle = spectator.debugElement.query(By.css('div.card > div.card-header'));
    expect(cardTitle.nativeElement.innerText.includes('Chemical Measurement')).toBeTruthy();
    expect(spectator.query('div#meta-info-container > table > tbody > tr > td')).toHaveText('Shape');
    expect(spectator.query('div#meta-info-container > table > tbody > tr > td:last-child')).toHaveText('4,  1');
  });

  it('should render data variables table', () => {
    expect(spectator.query('div.card:nth-child(2) > div.card-header')).toHaveText('Data Variables (2)');
    expect(spectator.queryAll('table#data-vars-container > tbody > tr')).toHaveLength(2);
    expect(spectator.query('table#data-vars-container > tbody > tr:last-child > td:nth-child(2)'))
      .toHaveText('Below  , Relative=detection limit');
    expect(spectator.query('table#data-vars-container > tbody > tr > td:last-child')).toHaveText('milligram per liter');
  });

  it('should render dim var tables', () => {
    expect(spectator.queryAll('table.dim-var-container')).toHaveLength(2);
    expect(spectator.query('div.dimension-type-container > h5')).toHaveText('Environmental Sample, size=4');
    expect(spectator.queryAll('table.dim-var-container > tbody > tr')).toHaveLength(5);
    expect(spectator.query('table.dim-var-container > tbody > tr > td:nth-child(2)')).toHaveText('Environmental Sample ID');
    expect(spectator.query('table.dim-var-container > tbody > tr > td:nth-child(4)')).toHaveText('N/A');
  });

  it('should render attributes table', () => {
    expect(spectator.queryAll('table#properties-container > tbody > tr')).toHaveLength(1);
    const tableRow = spectator.debugElement.query(By.css('table#properties-container > tbody > tr'))
    expect (tableRow.nativeElement).toHaveDescendantWithText({
      selector: 'td',
      'text': 'Data Variables Type'
    });
    expect(tableRow.nativeElement).toHaveDescendantWithText({
      selector: 'td:nth-child(2)',
      text: 'Measurement'
    });
    expect(tableRow.nativeElement).toHaveDescendantWithText({
      selector: 'td:last-child',
      text: 'N/A'
    });
  });

  it('should get core object refs and display', fakeAsync(() => {
    const uploadService = spectator.fixture.debugElement.injector.get(UploadService);
    spyOn(uploadService, 'getRefsToCoreObjects').and.callThrough();
    spectator.component.ngOnInit();
    spectator.detectChanges();
    expect(uploadService.getRefsToCoreObjects).toHaveBeenCalled();
    tick();
    spectator.detectChanges();

    expect(spectator.component.coreObjectRefs).toHaveLength(2);
    expect(spectator.component.totalObjectsMapped).toBe(150);
    expect(spectator.component.brick.coreObjectRefsError).toBeFalsy();

    expect(spectator.queryAll('table#core-object-refs-container > tbody > tr')).toHaveLength(2);
    const tableRow = spectator.debugElement.query(By.css('table#core-object-refs-container > tbody > tr'));
    expect(tableRow.nativeElement).toHaveDescendantWithText({
      selector: 'td',
      text: 'Environmental Sample ID'
    });
    expect(tableRow.nativeElement).toHaveDescendantWithText({
      selector: 'td:last-child',
      text: '100'
    });
  }));

  it('should render error if no core objects are mapped', fakeAsync(() => {
    mockCoreObjectRefs = [];
    const uploadService = spectator.fixture.debugElement.injector.get(UploadService);
    spyOn(uploadService, 'getRefsToCoreObjects').and.callThrough();
    spectator.component.ngOnInit();
    spectator.detectChanges();
    expect(uploadService.getRefsToCoreObjects).toHaveBeenCalled();
    tick();
    spectator.detectChanges();

    expect(spectator.component.coreObjectRefs).toHaveLength(0);
    expect(spectator.component.totalObjectsMapped).toBe(0);
    expect(spectator.component.brick.coreObjectRefsError).toBeTruthy();

    expect(spectator.query('div.alert.alert-danger')).not.toBeNull();
    expect(spectator.query('div.card:last-child > div.card-header')).toHaveClass('error-header');
  }));
});
