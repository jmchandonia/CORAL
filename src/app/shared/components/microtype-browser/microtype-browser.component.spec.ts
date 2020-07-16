import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NgxSpinnerModule } from 'ngx-spinner';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { MicrotypeBrowserComponent } from './microtype-browser.component';
import { HttpClientModule } from '@angular/common/http';
// TODO: give permanent URL for mock_microtypes, this link is not in repository
const mock_microtypes = require('src/app/shared/test/mock_microtypes_3.json');
import { MicrotypeTreeService } from 'src/app/shared/services/microtype-tree.service';
import { MicrotypeTreeFactoryService as MicrotypeTreeFactory } from 'src/app/shared/services/microtype-tree-factory.service';


describe('MicrotypeBrowserComponent', () => {
  let spectator: Spectator<MicrotypeBrowserComponent>;
  const createComponent = createComponentFactory({
    component: MicrotypeBrowserComponent,
    imports: [
      NgxSpinnerModule,
      HttpClientModule
    ],
    providers: [
      {
        provide: MicrotypeTreeService,
        useValue: {
          getMicrotypes: () => Promise.resolve(MicrotypeTreeFactory.createMicrotypeTree(mock_microtypes.results))
        }
      }]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should have proper tree structure', async(() => {
    const treeService = spectator.get(MicrotypeTreeService);
    spyOn(treeService, 'getMicrotypes').and.callThrough();
    spectator.detectChanges();

    spectator.fixture.whenStable().then(() => {
      spectator.detectChanges();
      expect(spectator.component.microtypes).toHaveLength(31);
    });

    spectator.component.ngOnInit();
    expect(treeService.getMicrotypes).toHaveBeenCalled();
  }));
});
